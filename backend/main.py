from fastapi import FastAPI

app = FastAPI()

@app.get('/')
def home():
    return "{'mensagem': 'Olá'}"

#Faça uma API para uma calculadora com as seguintes rotas e retornos:
#- rota: /soma : recebe dois inteiros A e B e retorna o resultado
@app.get("/soma")
def soma(a: int, b:int) -> str:
    res = a + b
    return f"Resultado da Soma: {res}" 

#- rota: /subtracao : recebe dois inteiros A e B e retorna o resultado
@app.get("/subtração")
def subtração(a: int, b:int) -> str:
    res = a - b 
    return f"Resultado da Subtração: {res}"
#- rota: /divisao : recebe dois inteiros A e B e retorna o resultado
@app.get("/divisao")
def divisao(a: int, b:int) -> str: 
    res = a / b
    return f"Resultado da Divisão: {res}"

#- rota: /multiplicacao : recebe dois inteiros A e B e retorna o resultado
@app.get("/multiplicacao")
def multiplicacao(a: int, b:int) -> str:
    res = a * b
    return f"Resultado da Multiplicao: {res}"

#- rota: /raiz : recebe um inteiro e retorna o resultado da raiz quadrada
@app.get("/raiz")
def raiz(a:int) -> str:
    res = a ** (1/2)
    return f"Resiçtadp da Raiz Quadrada: {res:.2f}"