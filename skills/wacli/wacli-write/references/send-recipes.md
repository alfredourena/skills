# Send Recipes

All sends affect WhatsApp remote state. Confirm target and content first.

## Text

```bash
WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"send text","target":"recipient","effect":"WhatsApp remote state"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \
  --account "$ACCOUNT" send text \
  --to "$RECIPIENT" \
  --message "$MESSAGE"
```

## File

```bash
WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"send file","target":"recipient","effect":"WhatsApp remote state"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \
  --account "$ACCOUNT" send file \
  --to "$RECIPIENT" \
  --file "$PATH" \
  --caption "$CAPTION"
```

## Sticker Or Voice

```bash
WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"send sticker","target":"recipient","effect":"WhatsApp remote state"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \
  --account "$ACCOUNT" send sticker --to "$RECIPIENT" --file "$PATH"

WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"send voice","target":"recipient","effect":"WhatsApp remote state"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \
  --account "$ACCOUNT" send voice --to "$RECIPIENT" --file "$PATH"
```

## Reaction

```bash
WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"send reaction","target":"chat message","effect":"WhatsApp remote state"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \
  --account "$ACCOUNT" send react \
  --to "$CHAT" \
  --id "$MSG_ID" \
  --reaction "$REACTION"
```

## Poll

```bash
WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"send poll","target":"recipient","effect":"WhatsApp remote state"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \
  --account "$ACCOUNT" send poll \
  --to "$RECIPIENT" \
  --question "$QUESTION" \
  --option "$OPTION_A" \
  --option "$OPTION_B"
```

## Status

```bash
WACLI_WRITE_ACK="I understand this may mutate WhatsApp or local Wacli state" \
WACLI_WRITE_CONFIRMATION='{"account":"personal","action":"send status","target":"status audience","effect":"WhatsApp remote state"}' \
python3 ~/.agents/skills/wacli-write/scripts/wacli_write_guard.py \
  --account "$ACCOUNT" send status --message "$MESSAGE"
```

Report the returned message ID as "accepted by WhatsApp", not delivered or read.
