#!/bin/bash
# Firewall initialization script for Debussy sandbox
# Based on Anthropic's Claude Code devcontainer firewall
# https://github.com/anthropics/claude-code/blob/main/.devcontainer/init-firewall.sh

set -euo pipefail

# Function to validate IP address or CIDR
validate_ip_or_cidr() {
    local ip="$1"
    # Match IPv4 address or CIDR notation
    if [[ "$ip" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}(/[0-9]{1,2})?$ ]]; then
        return 0
    fi
    return 1
}

# Function to add IP to ipset with validation
add_to_ipset() {
    local setname="$1"
    local ip="$2"
    if validate_ip_or_cidr "$ip"; then
        ipset add "$setname" "$ip" 2>/dev/null || true
    fi
}

echo "Initializing firewall..."

# Preserve Docker's DNS rules before flushing
DOCKER_DNS_RULES=$(iptables-save | grep -E "DOCKER|docker" || true)

# Flush existing rules
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X

# Restore Docker DNS rules if any
if [ -n "$DOCKER_DNS_RULES" ]; then
    echo "$DOCKER_DNS_RULES" | iptables-restore -n 2>/dev/null || true
fi

# Create ipset for allowed domains
ipset destroy allowed_hosts 2>/dev/null || true
ipset create allowed_hosts hash:net

# Always allow localhost
add_to_ipset allowed_hosts "127.0.0.0/8"

# DNS servers (common public DNS)
add_to_ipset allowed_hosts "8.8.8.8"
add_to_ipset allowed_hosts "8.8.4.4"
add_to_ipset allowed_hosts "1.1.1.1"
add_to_ipset allowed_hosts "1.0.0.1"

# GitHub API - fetch current IP ranges
echo "Fetching GitHub IP ranges..."
GITHUB_IPS=$(curl -s https://api.github.com/meta 2>/dev/null | jq -r '.web[], .api[], .git[]' 2>/dev/null || true)
for ip in $GITHUB_IPS; do
    add_to_ipset allowed_hosts "$ip"
done

# NPM registry
for ip in $(dig +short registry.npmjs.org 2>/dev/null || true); do
    add_to_ipset allowed_hosts "$ip"
done

# Anthropic API and OAuth endpoints
for ip in $(dig +short api.anthropic.com 2>/dev/null || true); do
    add_to_ipset allowed_hosts "$ip"
done
for ip in $(dig +short console.anthropic.com 2>/dev/null || true); do
    add_to_ipset allowed_hosts "$ip"
done
for ip in $(dig +short claude.ai 2>/dev/null || true); do
    add_to_ipset allowed_hosts "$ip"
done
# Statsig (Claude Code telemetry)
for ip in $(dig +short api.statsig.com 2>/dev/null || true); do
    add_to_ipset allowed_hosts "$ip"
done

# Sentry (for error reporting)
for ip in $(dig +short sentry.io 2>/dev/null || true); do
    add_to_ipset allowed_hosts "$ip"
done

# VS Code marketplace
for ip in $(dig +short marketplace.visualstudio.com 2>/dev/null || true); do
    add_to_ipset allowed_hosts "$ip"
done

# PyPI (for Python packages)
for ip in $(dig +short pypi.org 2>/dev/null || true); do
    add_to_ipset allowed_hosts "$ip"
done
for ip in $(dig +short files.pythonhosted.org 2>/dev/null || true); do
    add_to_ipset allowed_hosts "$ip"
done

# Get host network for local communication
HOST_NETWORK=$(ip route | grep default | awk '{print $3}' | head -1)
if [ -n "$HOST_NETWORK" ]; then
    # Allow the entire subnet
    HOST_SUBNET=$(echo "$HOST_NETWORK" | sed 's/\.[0-9]*$/.0\/24/')
    add_to_ipset allowed_hosts "$HOST_SUBNET"
fi

# Set default policies to DROP
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT DROP

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow DNS (port 53)
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT

# Allow SSH (port 22)
iptables -A OUTPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTPS to whitelisted hosts
iptables -A OUTPUT -p tcp --dport 443 -m set --match-set allowed_hosts dst -j ACCEPT
iptables -A OUTPUT -p tcp --dport 80 -m set --match-set allowed_hosts dst -j ACCEPT

echo "Firewall initialized successfully."

# Verification
echo "Testing firewall..."
if curl -s --connect-timeout 2 https://example.com >/dev/null 2>&1; then
    echo "WARNING: example.com is reachable (should be blocked)"
else
    echo "OK: example.com blocked"
fi

if curl -s --connect-timeout 5 https://api.github.com >/dev/null 2>&1; then
    echo "OK: api.github.com reachable"
else
    echo "WARNING: api.github.com unreachable (should be allowed)"
fi

echo "Firewall setup complete."
