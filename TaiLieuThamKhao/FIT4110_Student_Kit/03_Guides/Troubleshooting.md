# Troubleshooting

| Symptom | Check | Safe next step |
|---|---|---|
| Docker daemon unavailable | `docker info` | Start Docker Desktop/Engine and wait until ready. |
| Port already in use | `lsof -i :8000` / `netstat -ano \| findstr :8000` | Stop the identified lab container or choose a documented alternate port. |
| Compose service unhealthy | `docker compose ps`; `docker compose logs <service>` | Fix the first error; check env values and dependency healthchecks. |
| Prism/Newman fails | `node --version`; `npm install` | Confirm Node LTS and paths in the environment file. |
| OpenAPI lint fails | run the supplied lint command | Fix the reported line; do not suppress a rule without rationale. |
| Push rejected | `git remote -v`; `git status` | Ensure `origin` is your personal repository and pull/rebase only after understanding divergence. |

Record unresolved problems in `known-issues.md`: symptom, command, evidence, attempted fix, owner, and next action. A documented limitation is better than a silent omission.

## Bản dịch tiếng Việt

Ghi lỗi chưa xử lý vào `known-issues.md` gồm hiện tượng, lệnh tái hiện, minh chứng, cách đã thử, người phụ trách và bước tiếp theo. Lỗi được mô tả rõ tốt hơn lỗi bị bỏ qua.
