# ---- Build stage ----
FROM ubuntu:24.04 AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc make libc6-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY fiche.c fiche.h main.c Makefile ./

RUN make

# ---- Runtime stage ----
FROM ubuntu:24.04

RUN useradd --system --no-create-home --shell /usr/sbin/nologin fiche && \
    mkdir -p /data && \
    chown fiche:fiche /data

COPY --from=builder /build/fiche /usr/local/bin/fiche

# /data is the directory where pastes are stored.
# Mount a host directory or a named volume here for persistence.
VOLUME /data

USER fiche

EXPOSE 9999

ENTRYPOINT ["fiche"]
CMD ["-o", "/data"]
