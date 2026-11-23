# Lab 1 · Esqueleto iJanta + bucket de comprovantes seguro

Objetivo: criar um bucket S3 seguro para os comprovantes de pagamento da iJanta **sem digitar uma linha de HCL**.
Quem escreve é o OpenCode; quem lê, aprova e valida é você.

> **Antes do primeiro prompt.** Só o código deste repositório da iJanta entra no agente. Nada de código ou dado da sua
> empresa, IPs, nomes de clientes ou saída de `plan` real. A chave do AI Studio fica só na variável de
> ambiente: nunca no prompt, num chat ou num print.

## Passos

1. Abra o Codespace do seu repositório (**Code → Codespaces**) e, no terminal, na raiz do repositório, rode:

   ```bash
   opencode
   ```

   Quem instalou tudo localmente pode usar o próprio terminal, sempre na raiz do repositório.

2. **Etapa 1:** cole o prompt da etapa 1 (abaixo). O agente cria `provider.tf` e `variables.tf`.
3. **Etapa 2:** cole o prompt restrito da etapa 2. O agente cria `s3_comprovantes.tf`.
4. **Leia cada mudança antes de aprovar.** O OpenCode pede aprovação (`ask`) antes de editar arquivo ou
   rodar comando. Confira o diff contra o checklist. Se algo estiver fora, recuse e peça a correção.
5. Valide no terminal (fora do OpenCode, ou aprovando o comando nele):

   ```bash
   terraform init -backend=false
   terraform validate
   ```

   Ninguém precisa de conta AWS: `-backend=false` e o `validate` não acessam a nuvem.

## Prompts

### Etapa 1 · provider e variáveis

```text
Papel: engenheiro de IaC sênior.
Tarefa: crie provider.tf e variables.tf para a iJanta.
Restrições:
- terraform required_version >= 1.10 e provider hashicorp/aws com version "~> 6.0"
- provider "aws" com region = var.region e default_tags com Project = "ijanta" e Env = var.environment
- variables.tf: region (string, default "us-east-1") e environment (string, default "dev"),
  ambas com description e type
- nenhum backend, nenhuma credencial, nenhum profile
Formato: só HCL, sem explicação. Antes de editar, liste os arquivos que vai criar.
```

### Etapa 2 · bucket de comprovantes (prompt restrito)

```text
Papel: engenheiro de IaC sênior, foco em segurança.
Tarefa: gere s3_comprovantes.tf para a iJanta.
Contexto: o bucket guarda comprovantes de pagamento. O recurso principal se chama
aws_s3_bucket.comprovantes e o nome do bucket usa var.environment.
Restrições:
- versioning, Block Public Access e encryption
  como recursos aws_s3_bucket_* separados
- nenhuma ACL pública; nenhuma credencial no código
- só argumentos da documentação do provider
Formato: só HCL, sem explicação.
```

As cinco partes (papel, tarefa, contexto, restrições, formato) são as da lição L2 do pre-work.
Cada restrição vira um item que você confere no diff.

## Checklist

| # | Atributo | Recurso separado | O que conferir |
|---|----------|------------------|----------------|
| 1 | Versioning | `aws_s3_bucket_versioning` | `status = "Enabled"` |
| 2 | Block Public Access | `aws_s3_bucket_public_access_block` | `block_public_acls`, `block_public_policy`, `ignore_public_acls`, `restrict_public_buckets`, todos `true` |
| 3 | Encryption | `aws_s3_bucket_server_side_encryption_configuration` | regra com `apply_server_side_encryption_by_default` |

Os três apontam para `aws_s3_bucket.comprovantes.id`. Nenhum deles fica como bloco dentro do `aws_s3_bucket`.

## Pronto quando

- [ ] `terraform validate` retorna `Success! The configuration is valid.`
- [ ] Os 3 atributos do checklist aparecem como recursos separados
- [ ] O print **não** mostra a chave do AI Studio nem nenhum tfstate

### Entrega do M1

O formulário da avaliação do M1 pede um print com o `Success` do validate **e** o código de `s3_comprovantes.tf` mostrando os 3 recursos
(ou a saída do Checkov com os checks de versioning, Block Public Access e encryption em `PASSED`).
Antes de capturar, confira: terminal sem `echo $GOOGLE_GENERATIVE_AI_API_KEY`, sem `env`, sem arquivo `.tfstate` aberto.

## Sensor extra (opcional)

```bash
checkov -f s3_comprovantes.tf --compact
```

Espere alguns `FAILED` que **não** fazem parte do checklist: access logging (CKV_AWS_18), replicação entre
regiões (CKV_AWS_144), KMS em vez de AES256 (CKV_AWS_145), lifecycle (CKV2_AWS_61) e event notifications
(CKV2_AWS_62). São decisões de custo e operação que o time precisa tomar: o sensor aponta, você decide.
O que precisa passar é o Block Public Access (CKV2_AWS_6) e a ausência de ACL pública (CKV_AWS_20).

## Travou? Use na ordem

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

## Terminou antes?

- Rode o mesmo prompt da etapa 2 de novo, num arquivo temporário, e compare as duas saídas com `diff`.
  O mesmo prompt gera código diferente: a saída do modelo é probabilística.
- Faça o [desafio do MiniStack](../desafio/README.md#b-plan-apply-e-destroy-no-ministack):
  plan, apply e destroy deste bucket num emulador local de AWS.
