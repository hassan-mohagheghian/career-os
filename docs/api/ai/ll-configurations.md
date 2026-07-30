# LLM Configurations API

## Purpose

Manage reusable LLM Configurations.

Executor and Provider are fixed by the system.

---

## Endpoints

### Get Configurations

GET /api/llm-configurations

Returns all configurations.

---

### Get Configuration

GET /api/llm-configurations/{id}

Returns a single configuration.

---

### Create Configuration

POST /api/llm-configurations

#### Request

```json
{
  "name": "Production GPT-5",
  "model": "gpt-5",
  "model_version": "2027-01",
  "enabled": true
}
```

#### Response

```json
{
  "id": "0197a7cf-73b0-7df0-b1a3-9af2c61c1d52"
}
```

---

### Update Configuration

PATCH /api/llm-configurations/{id}

Updates one or more fields.

---

### Delete Configuration

DELETE /api/llm-configurations/{id}

Deletes a configuration.

---

## Validation

Required

- name
- model

Optional

- model_version
- enabled

---

## Error Codes

| Status | Description                       |
| ------ | --------------------------------- |
| 400    | Validation failed                 |
| 404    | Configuration not found           |
| 409    | Configuration is currently in use |
| 500    | Internal Server Error             |
