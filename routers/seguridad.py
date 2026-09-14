from pwdlib import PasswordHash

password_hash = PasswordHash.recommended() #crea un objeto segun las recomendaciones de la libreria para hashear la contra

def hashear_contrasena(contrasena: str) -> str: #dice que esta pensando para un str 
    return password_hash.hash(contrasena) #hashea la contrasena

def verificar_contrasena( contrasena_ingresada: str, contrasena_hasheada: str) -> bool:
    return password_hash.verify( #compara con la contrasena normal con la hasheada
        contrasena_ingresada,
        contrasena_hasheada
    )
