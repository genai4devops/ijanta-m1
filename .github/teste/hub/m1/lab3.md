# Lab 3 · VPC da API de pedidos com harness · dicas e solução

Enunciado: [ijanta-m1/labs/lab3-vpc](https://github.com/genai4devops/ijanta-m1/tree/main/labs/lab3-vpc). Abra na ordem e só o que precisar.

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
