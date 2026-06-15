sed -i 's/curl -f http:\/\/127.0.0.1:6333\/healthz/wget -qO- http:\/\/127.0.0.1:6333\/healthz/g' .github/workflows/ci.yml
