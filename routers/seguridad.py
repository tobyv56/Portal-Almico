from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

def hashear_contrasena(contrasena: str) -> str:
    return password_hash.hash(contrasena)

def verificar_contrasena( contrasena_ingresada: str, contrasena_hasheada: str) -> bool:
    return password_hash.verify(
        contrasena_ingresada,
        contrasena_hasheada
    )