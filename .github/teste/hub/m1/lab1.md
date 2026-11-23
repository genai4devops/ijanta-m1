# Lab 1 · Esqueleto iJanta + bucket de comprovantes seguro · dicas e solução

Enunciado: [ijanta-m1/labs/lab1-s3](https://github.com/genai4devops/ijanta-m1/tree/main/labs/lab1-s3). Abra na ordem e só o que precisar.

<details>
<summary><b>Hint 1</b> · o validate falhou</summary>

- `Error: Unsupported argument`: o agente inventou um argumento ou usou um bloco antigo. Copie a mensagem
  de erro para o OpenCode e peça a correção citando a restrição "só argumentos da documentação do provider".
- `Error: Missing required provider` ou `Plugins are not installed`: você rodou o validate sem o
  `terraform init -backend=false`.
- O OpenCode não responde ou reclama de chave: confira se a variável existe **sem imprimir o valor**:
  `test -n "$GOOGLE_GENERATIVE_AI_API_KEY" && echo ok`.

</details>

<details>
<summary><b>Hint 2</b> · o validate passa, mas o checklist não fecha</summary>

- Encryption ou versioning ficaram como bloco dentro de `aws_s3_bucket`? Recuse o diff e peça:
  "separe em aws_s3_bucket_versioning e aws_s3_bucket_server_side_encryption_configuration, como diz a restrição".
- Block Public Access com menos de 4 flags? Peça explicitamente as quatro: `block_public_acls`,
  `block_public_policy`, `ignore_public_acls`, `restrict_public_buckets`.
- Apareceu `acl = "private"` ou um `aws_s3_bucket_acl`? Não é necessário: remova. O Block Public Access já cobre o risco.

</details>

<details>
<summary><b>Solução</b> · <code>provider.tf</code>, <code>variables.tf</code> e <code>s3_comprovantes.tf</code> de referência</summary>

`provider.tf`:

```hcl
terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project = "ijanta"
      Env     = var.environment
    }
  }
}
```

`variables.tf`:

```hcl
variable "region" {
  description = "Região AWS da iJanta"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
  default     = "dev"
}
```

`s3_comprovantes.tf`:

```hcl
resource "aws_s3_bucket" "comprovantes" {
  bucket = "ijanta-comprovantes-${var.environment}"
}

resource "aws_s3_bucket_versioning" "comprovantes" {
  bucket = aws_s3_bucket.comprovantes.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "comprovantes" {
  bucket = aws_s3_bucket.comprovantes.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "comprovantes" {
  bucket = aws_s3_bucket.comprovantes.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
```

As tags vêm do `default_tags` do provider (etapa 1), por isso não aparecem aqui.

</details>
