#!/bin/bash

# Install LitmusChaos for Kubernetes chaos engineering
# This script installs LitmusChaos operator and chaos experiments

set -e

echo "🚀 Installing LitmusChaos for chaos engineering..."

# Install LitmusChaos operator
kubectl apply -f https://litmuschaos.github.io/litmus/litmus-operator-v1.13.8.yaml

# Wait for operator to be ready
echo "⏳ Waiting for LitmusChaos operator to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/litmus-operator -n litmus

# Install chaos experiments
kubectl apply -f https://hub.litmuschaos.io/api/chaos/1.13.8?file=charts/generic/experiments.yaml

# Create chaos namespace if it doesn't exist
kubectl create namespace chaos --dry-run=client -o yaml | kubectl apply -f -

# Install chaos experiments in chaos namespace
kubectl apply -f https://hub.litmuschaos.io/api/chaos/1.13.8?file=charts/generic/experiments.yaml -n chaos

echo "✅ LitmusChaos installed successfully!"
echo "📋 Available chaos experiments:"
kubectl get chaosexperiments -n chaos