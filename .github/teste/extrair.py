"""Monta na raiz os arquivos das soluções dos READMEs dos labs (teste temporário)."""
import re, sys, pathlib

raiz = pathlib.Path(sys.argv[1])
padrao = re.compile(r"^`([\w.]+\.tf)`( \(acrescentar\))?:\n\n```hcl\n(.*?)```", re.S | re.M)
for lab in ["lab1-s3", "lab2-iam", "lab3-vpc"]:
    texto = (raiz / "labs" / lab / "README.md").read_text()
    for nome, acrescentar, codigo in padrao.findall(texto):
        destino = raiz / nome
        modo = "a" if acrescentar else "w"
        with destino.open(modo) as f:
            f.write(("\n" if acrescentar else "") + codigo)
        print(f"{lab}: {nome} ({'acrescentado' if acrescentar else 'escrito'})")
