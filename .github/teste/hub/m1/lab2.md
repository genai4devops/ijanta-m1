# Lab 2 · Auditoria IAM do worker de pagamentos · dicas e solução

Enunciado: [ijanta-m1/labs/lab2-iam](https://github.com/genai4devops/ijanta-m1/tree/main/labs/lab2-iam). Abra na ordem e só o que precisar.

<details>
<summary><b>Hint 1</b> · o agente trocou o curinga por uma lista enorme</summary>

O agente às vezes troca `"*"` por 20 ações "por garantia". Peça: "justifique cada ação com um uso
real do worker de pagamentos; remova as que não tiverem uso". O worker lê comprovante, grava comprovante
e, no máximo, lista o bucket.

</details>

<details>
<summary><b>Hint 2</b> · o Checkov ainda reclama, ou o validate quebrou</summary>

- `Reference to undeclared resource`: o `s3_comprovantes.tf` do Lab 1 não está na raiz, ou o recurso
  não se chama `comprovantes`.
- Checkov ainda falha em CKV_AWS_355: sobrou algum `Resource = "*"`. Procure com `grep -n '"\*"' iam_policy.tf`.
- `GetObject`/`PutObject` precisam do ARN **com** `/*` (objetos). `ListBucket` precisa do ARN **sem** `/*` (o bucket).
- ARN escrito à mão (`arn:aws:s3:::ijanta-...`)? Troque pela referência ao recurso.

</details>

<details>
<summary><b>Solução</b> · <code>iam_policy.tf</code> de referência</summary>

`iam_policy.tf`:

```hcl
resource "aws_iam_policy" "pagamentos" {
  name = "ijanta-pagamentos-worker"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "LerEGravarComprovantes"
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject"]
        Resource = "${aws_s3_bucket.comprovantes.arn}/*"
      },
      {
        Sid      = "ListarComprovantes"
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = aws_s3_bucket.comprovantes.arn
      }
    ]
  })
}
```

Se o seu bucket usar KMS em vez de AES256, o worker também precisa de `kms:Decrypt` e
`kms:GenerateDataKey` na chave. A solução do Lab 1 usa AES256 para manter a policy mínima.

</details>
