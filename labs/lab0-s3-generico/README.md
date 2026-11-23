# Lab 0 · Um S3 que parece certo

O arquivo [`s3_generico.tf`](s3_generico.tf) foi gerado por um pedido curto, sem restrições:

```text
crie um bucket S3 em Terraform para os comprovantes da iJanta
```

O bucket vai guardar comprovantes de pagamento de clientes. O código tem pelo menos três problemas.

## Passos

1. Leia o arquivo e anote os três problemas antes de rodar qualquer ferramenta.
2. Nesta pasta, rode o sensor de sintaxe:

   ```bash
   cd labs/lab0-s3-generico
   terraform init -backend=false
   terraform validate
   ```

3. Remova a linha que o `validate` apontou e rode o `validate` de novo.
4. Compare o resultado com a sua lista. Quais problemas continuam no arquivo?
5. Desfaça a alteração: `git checkout -- s3_generico.tf`.

Não copie este arquivo para a raiz do repositório: ele é só para este exercício.

<details>
<summary><b>Respostas</b></summary>

| Linha | Problema | Tipo | O `validate` pega? |
|-------|----------|------|--------------------|
| `auto_encrypt = true` | O argumento não existe no provider | Alucinação | Sim: `Unsupported argument` |
| `versioning { ... }` | Bloco inline depreciado desde o provider v4; hoje é o recurso `aws_s3_bucket_versioning` | Legado | Não |
| `acl = "public-read"` | Válido, roda, e deixa os comprovantes legíveis por qualquer pessoa | Risco | Não |

Depois de remover o argumento inventado, o `validate` retorna `Success`, e a ACL pública continua lá.
`validate` verde quer dizer sintaxe válida, não bucket seguro. O [Lab 1](../lab1-s3/README.md) corrige os três.

Fontes: [guia de upgrade v4 do provider AWS](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/guides/version-4-upgrade),
[`aws_s3_bucket_versioning`](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_versioning),
[`terraform validate`](https://developer.hashicorp.com/terraform/cli/commands/validate).

</details>
