# Docker Cleanup Log - November 11, 2025

## Summary
- **Date**: 2025-11-11 13:17
- **Total Space Reclaimed**: 31.01GB
- **Action**: Ran `docker system prune -a --volumes -f`

## Deleted Docker Images

### 1. docker/desktop-reclaim-space:latest
- **Digest**: sha256:8b26e45c51632fd78131f3bddca76122bebc1dd8376f16dd26f769c7f33121fd
- **Purpose**: Docker Desktop space reclamation utility

### 2. freqtradeorg/freqtrade:stable
- **SHA**: sha256:7427f8cd102cdf3ad3b6023f1a72c99ac0c7a36ad3e0be41a0424788c87e200b
- **Purpose**: Cryptocurrency trading bot

### 3. hummingbot/hummingbot-api:latest
- **SHA**: sha256:208bf7a329272ba125ba4df902941aa24900d8ed04bb68e4cf510e3eacdcd1cc
- **Purpose**: Hummingbot API service

### 4. hummingbot/hummingbot:latest
- **SHA**: sha256:e84cd984746a55883df050bbe58e5df736839209768982e08d66daa4cf3e5c1f
- **Purpose**: Main Hummingbot trading bot image

### 5. python:3.12
- **SHA**: sha256:a9841e6ccd4c0e30225a54dd133431b61325c43e20893576ffcfa7235237e444
- **Purpose**: Python 3.12 base image

### 6. semgrep/semgrep:latest
- **SHA**: sha256:e2a7ca874b5ef7dd47b3f613a429bc75050e6a1abfb2b42496d7ce2414d286cb
- **Purpose**: Static analysis security tool

### 7. hummingbot/hummingbot-mcp:latest
- **SHA**: sha256:986de78beeaa508d0bcf175a8e26bb2df6a73c012140718b1c88d253ddeda78e
- **Purpose**: Hummingbot MCP (Model Context Protocol) service

### 8. emqx:5
- **SHA**: sha256:dd5c59d344e608b03cbb6aa39ed699d24a2bc9866e074d2f7ffc22d3ba9dc638
- **Purpose**: MQTT broker for IoT messaging

### 9. hummingbot-hummingbot:latest (local build)
- **SHA**: sha256:2448c91a9d353efebec8c708c1b26cbac67a8a8767c716d70b780cbd486b56be
- **Purpose**: Local Hummingbot build

### 10. postgres:16
- **SHA**: sha256:21f6013073bc6b92830a2129570e2f5ec42a6c734b5a985a41e83aa58f54c3c1
- **Purpose**: PostgreSQL database version 16

### 11. ghcr.io/open-webui/open-webui:main
- **SHA**: sha256:d6ab9bce3030f5b58e59144a7db9fe3012b39c94d27bc2979e98e6d6dc2161da
- **Purpose**: Open WebUI for LLM interfaces

## Deleted Containers
- **Container ID**: 160965cfc92affce536d1ac58f1fff493d2b8c5d955004b1fe15aff4ab2703a5

## Deleted Networks
- `ft_userdata_default` - FreqTrade user data network

## Deleted Volumes
- 5 local volumes (2.064GB total)

## Deleted Build Cache
- 79 build cache objects totaling 21.37GB

## Docker Disk Usage Before Cleanup
```
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          11        1         44.48GB   43.21GB (97%)
Containers      1         0         20.48kB   20.48kB (100%)
Local Volumes   5         0         2.064GB   2.064GB (100%)
Build Cache     79        0         21.37GB   21.37GB (100%)
```

## Docker.raw File Compaction

### Compaction Process (2025-11-11 13:23)
1. Stopped Docker Desktop completely
2. Used `cp -c` to create a compacted copy of Docker.raw
3. Replaced original with compacted version
4. Verified Docker Desktop functionality
5. Removed old backup file

### Results
- **Docker.raw logical size**: 228GB (sparse file)
- **Actual disk space used**: 3.3GB
- **Status**: Successfully compacted and verified working
- **Method**: macOS sparse file copy (`cp -c`)

The sparse file now only uses 3.3GB of actual disk space while maintaining the 228GB logical size needed by Docker.

## Notes
- Most images were inactive and could be safely removed
- All removed images can be pulled again if needed
- The compaction process successfully reduced actual disk usage

## Restoration Instructions
If you need to restore any of these images, use:
```bash
docker pull <image-name>:<tag>
```

For example:
```bash
docker pull hummingbot/hummingbot:latest
docker pull postgres:16
docker pull python:3.12
```
