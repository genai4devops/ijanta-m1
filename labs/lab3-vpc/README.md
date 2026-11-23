# Lab 3 · VPC da API de pedidos com harness

Objetivo: construir a rede da API de pedidos com o OpenCode, usando o [`AGENTS.md`](../../AGENTS.md) como
guide fixo e o `terraform validate` como sensor **ao fim de cada etapa**.

Arquitetura alvo:

```text
VPC (var.vpc_cidr)
├── subnet pública  us-east-1a ──┐
├── subnet pública  us-east-1b   ├── route table pública → Internet Gateway
│        └── NAT Gateway + Elastic IP (na pública da 1a)
├── subnet privada  us-east-1a ──┐
└── subnet privada  us-east-1b   └── route table privada → NAT Gateway
```

> ⚠️ **Este lab não usa AWS.** Se você rodar `apply` na sua própria conta, o NAT Gateway é cobrado por hora:
> faça `destroy` no fim.

## Passos

1. **Confirme que o OpenCode carregou o AGENTS.md.** Na raiz do repositório, abra o `opencode` e pergunte:

   ```text
   Quais regras do projeto você está seguindo? Liste-as sem editar nada.
   ```

   A resposta precisa citar as AZs fixas, as tags obrigatórias e a proibição de IAM. Se não citar, você
   provavelmente abriu o agente fora da raiz do repositório.

2. **Siga os 4 prompts, na ordem.** Aprove cada mudança só depois de ler o diff.
3. **No NAT, confira o `allocation_id`**: ele aponta para o Elastic IP (`aws_eip.<nome>.id`). É a
   referência que o modelo mais erra neste recurso.
4. **`terraform validate` verde ao fim de cada etapa.** O erro aparece perto de onde nasceu.

## Chain of prompts

Um prompt por camada. Pedir tudo de uma vez gera um diff grande demais para revisar.

### Etapa 1 · VPC e variáveis

```text
Crie vpc.tf com uma aws_vpc chamada "pedidos" para a API de pedidos da iJanta.
- CIDR em var.vpc_cidr (default "10.20.0.0/16"), declarada em variables.tf com description e type
- enable_dns_support e enable_dns_hostnames = true
- siga o AGENTS.md (tags, convenções)
Antes de editar, liste os arquivos que vai mudar. Só HCL.
```

### Etapa 2 · subnets

```text
Em vpc.tf, adicione 2 subnets públicas e 2 privadas na aws_vpc.pedidos.
- AZs fixas do AGENTS.md (uma pública e uma privada em cada AZ), sem data source
- CIDRs derivados de var.vpc_cidr com cidrsubnet
- tag Tier = "publica" ou "privada"
Só HCL.
```

### Etapa 3 · Internet Gateway, NAT com Elastic IP e rotas

```text
Em vpc.tf, adicione:
- aws_internet_gateway na aws_vpc.pedidos
- aws_eip para o NAT (domain = "vpc")
- aws_nat_gateway numa subnet pública, com allocation_id apontando para o EIP
- route table pública com 0.0.0.0/0 → Internet Gateway, associada às 2 públicas
- route table privada com 0.0.0.0/0 → NAT Gateway, associada às 2 privadas
Nenhum recurso IAM. Só HCL.
```

### Etapa 4 · outputs

```text
Crie outputs.tf com: vpc_id, public_subnet_ids, private_subnet_ids e nat_gateway_id.
Cada output com description. Não mude outros arquivos. Só HCL.
```

## Pronto quando

- [ ] `terraform validate` verde em todas as etapas
- [ ] `aws_nat_gateway` com `allocation_id` apontando para o Elastic IP
- [ ] Outputs em `outputs.tf` (nenhum `output` em outro arquivo)
- [ ] Nenhum recurso IAM novo; AZs `us-east-1a` e `us-east-1b` escritas no código

## Travou? Use na ordem

<details>
<summary><b>Hint 1</b> · AZs e subnets</summary>

- O agente trocou as AZs por `data "aws_availability_zones"`? Recuse: o AGENTS.md fixa as AZs, e o data
  source exigiria acesso à AWS. Peça para seguir a regra das AZs fixas.
- Duas subnets na mesma AZ? Confira o `availability_zone` de cada uma: precisa haver uma pública e uma
  privada em cada AZ.
- Duas subnets com o mesmo terceiro argumento no `cidrsubnet` (netnum) geram CIDRs sobrepostos. O
  `validate` **não** pega isso: só a AWS recusaria, no `apply`. Confira que cada subnet tem um número diferente.

</details>

<details>
<summary><b>Hint 2</b> · NAT e rotas</summary>

- `allocation_id = aws_eip.nat.id` (ID da alocação do EIP), não `aws_eip.nat.public_ip`.
- O NAT fica numa subnet **pública**: ele precisa de rota para o Internet Gateway.
- A rota privada usa `nat_gateway_id`; a pública usa `gateway_id`. O agente às vezes inverte.
- Associação esquecida: sem `aws_route_table_association`, a subnet usa a route table principal da VPC.

</details>

<details>
<summary><b>Solução</b> · <code>vpc.tf</code>, <code>outputs.tf</code> e variável de referência</summary>

`variables.tf` (acrescentar):

```hcl
variable "vpc_cidr" {
  description = "CIDR da VPC da API de pedidos"
  type        = string
  default     = "10.20.0.0/16"
}
```

`vpc.tf`:

```hcl
locals {
  azs = ["us-east-1a", "us-east-1b"]
}

resource "aws_vpc" "pedidos" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "ijanta-pedidos-${var.environment}" }
}

resource "aws_subnet" "publica" {
  count             = 2
  vpc_id            = aws_vpc.pedidos.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone = local.azs[count.index]

  tags = { Name = "ijanta-publica-${local.azs[count.index]}", Tier = "publica" }
}

resource "aws_subnet" "privada" {
  count             = 2
  vpc_id            = aws_vpc.pedidos.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = local.azs[count.index]

  tags = { Name = "ijanta-privada-${local.azs[count.index]}", Tier = "privada" }
}

resource "aws_internet_gateway" "pedidos" {
  vpc_id = aws_vpc.pedidos.id
  tags   = { Name = "ijanta-igw" }
}

resource "aws_eip" "nat" {
  domain = "vpc"
  tags   = { Name = "ijanta-nat-eip" }
}

resource "aws_nat_gateway" "pedidos" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.publica[0].id
  tags          = { Name = "ijanta-nat" }

  depends_on = [aws_internet_gateway.pedidos]
}

resource "aws_route_table" "publica" {
  vpc_id = aws_vpc.pedidos.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.pedidos.id
  }

  tags = { Name = "ijanta-rt-publica" }
}

resource "aws_route_table" "privada" {
  vpc_id = aws_vpc.pedidos.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.pedidos.id
  }

  tags = { Name = "ijanta-rt-privada" }
}

resource "aws_route_table_association" "publica" {
  count          = 2
  subnet_id      = aws_subnet.publica[count.index].id
  route_table_id = aws_route_table.publica.id
}

resource "aws_route_table_association" "privada" {
  count          = 2
  subnet_id      = aws_subnet.privada[count.index].id
  route_table_id = aws_route_table.privada.id
}
```

`outputs.tf`:

```hcl
output "vpc_id" {
  description = "ID da VPC da API de pedidos"
  value       = aws_vpc.pedidos.id
}

output "public_subnet_ids" {
  description = "IDs das subnets públicas"
  value       = aws_subnet.publica[*].id
}

output "private_subnet_ids" {
  description = "IDs das subnets privadas"
  value       = aws_subnet.privada[*].id
}

output "nat_gateway_id" {
  description = "ID do NAT Gateway"
  value       = aws_nat_gateway.pedidos.id
}
```

As tags `Project` e `Env` vêm do `default_tags` do provider (Lab 1). Um NAT só, na AZ 1a, é escolha de
custo; em produção, um NAT por AZ evita ponto único de falha.

</details>

## Terminou?

Veja o [desafio do M1](../desafio/README.md): A/B com e sem AGENTS.md, ou o MiniStack do Lab 1.
