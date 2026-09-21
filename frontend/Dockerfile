FROM node:22-bookworm-slim

ENV PNPM_HOME="/pnpm" \
    PATH="/pnpm:$PATH" \
    CI="true"

RUN corepack enable && corepack prepare pnpm@11.24.0 --activate

WORKDIR /app

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./
RUN pnpm install --frozen-lockfile

COPY . .

EXPOSE 5173

CMD ["pnpm", "dev", "--host", "0.0.0.0", "--port", "5173"]
