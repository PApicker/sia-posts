# Sia — автопостинг через GitHub Actions

Этот репозиторий работает в паре с десктоп-приложением Sia.
Sia складывает сюда отложенные посты, GitHub Actions раз в 30 минут постит то, чьё время пришло.

## Что внутри

- `posts/scheduled_posts.json` — очередь постов (заполняется Sia автоматически)
- `posts/images/` — приложенные картинки
- `cron_post.py` — Python-скрипт, выполняется в Actions
- `.github/workflows/scheduler.yml` — расписание (каждые 30 минут)

## Установка (одноразово)

### 1. Создай этот репо

GitHub → New repository → имя на твой вкус (`sia-posts`), **Public**, без README.
Затем загрузи в него всё содержимое этой папки (можно через `Add file → Upload files`).

### 2. Создай Personal Access Token (PAT)

github.com → Settings → Developer settings → **Personal access tokens → Fine-grained tokens** → **Generate new token**:
- Resource owner: твой аккаунт
- Repository access: **Only selected repositories** → выбери созданный репо
- Permissions → **Repository permissions** → **Contents** → **Read and write**
- Generate → скопируй `github_pat_xxx...` **СРАЗУ** (больше не покажет)

### 3. Бот в админы Telegram-канала

В Telegram открой свой канал → Manage Channel → Administrators → Add Administrator → найди своего бота по @username → разреши **Post Messages**.

### 4. Добавь secrets в репо

В этом репо: Settings → Secrets and variables → Actions → **New repository secret**:
- `TG_TOKEN` = твой Telegram Bot Token (тот же что в Sia)
- `TG_CHAT_ID` = твой Chat ID (`@your_channel` или числовой ID)

### 5. Подключи репо в Sia

Открой Sia → Настройки → секция **GitHub автопостинг**:
- `gh_repo` = `твой_логин/sia-posts`
- `gh_pat`  = `github_pat_xxx...` из шага 2

### 6. Готово

Теперь когда планируешь пост в Sia, она пушит в этот репо, Actions раз в 30 минут проверяет очередь и постит то, чьё время подошло.

## Проверка

- Actions → workflow «Post scheduled to Telegram» → должен быть зелёный
- Жми **Run workflow** вручную (workflow_dispatch) — проверь что не падает
- Поставь тестовый пост в Sia на «через 35 минут» — должен прийти в канал

## Точность времени

Cron `*/30 * * * *` = каждые 30 минут. Реальная отправка в течение 30 мин от запланированного. Для слотов 8/13/18 это норм.

Если хочешь точнее (±5 мин) — поменяй в `.github/workflows/scheduler.yml` на `*/5 * * * *`. Бесплатный лимит GitHub Actions — 2000 минут/мес, при 30-минутном cron уходит ~48 запусков/день × ~30 сек = 24 мин/день = 720 мин/мес. С запасом.

## Что НЕ делать

- Не клади в этот репо ключи API. Только TG_TOKEN/TG_CHAT_ID в **Secrets** (не в код).
- PAT в Sia хранится локально в `settings.json` — не пушь его в репо.
- Если PAT слил случайно — отзови его на github.com/settings/tokens и создай новый.
