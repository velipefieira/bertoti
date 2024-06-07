# pip install pytelegrambotapi
# pip install transformers
# pip install geopy

import telebot
from transformers import pipeline
from telebot import types
from geopy.geocoders import Nominatim

#API_TOKEN = '6694896297:AAHtDtk2-rtvW8G4uI7gLQAvvN56KU1ccVc' 
#bot = telebot.TeleBot(API_TOKEN)

API_TOKEN = '7050290039:AAEJBNlBqRc5jto3U4wimAOs5DWwdEc9DIY'
bot = telebot.TeleBot(API_TOKEN)

pedido = {
    "pizzas": [],
    "bebidas": [],
    "endereco": None,
    "valor": 0
}

bebidas_disponiveis = [
      "Refresh Cola - Cola",
      "Fizz Fusion - Guaraná",
      "Citrus Snap - Limão",
      "Orange Twist - Laranja"
]

pizzas_disponiveis = {
    "Calabresa": 49.99,
    "Margherita": 44.75,
    "Portuguesa": 44.99,
    "Frango com Catupiry": 47.99,
    "Calzone": 52.25,
    "Peperoni": 43.25,
    "Mussarela": 44.25,
    "Strogonoff": 44.99,
    "Chocolate": 44.99
}


geolocator = Nominatim(user_agent="PizzaPlanet")

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

intencoes = ["pizza", "bebida", "endereco", "cardapio", "encerrar"]


def identificar_intencao(texto):
    scores = classifier(texto, intencoes)
    return scores['labels'][0]

def identificar_pizza(texto):
    scores = classifier(texto, list(pizzas_disponiveis.keys()))
    return scores['labels'][0]

def identificar_bebida(texto):
    scores = classifier(texto, bebidas_disponiveis)
    return scores['labels'][0]

def buscar_menu():
    texto_opcoes = "Temos as seguintes opções:\nPizzas:\n"
    for nome, preco in pizzas_disponiveis.items():
        texto_opcoes += f"{nome} - R${round(preco, 2)}\n"
    texto_opcoes += f"\nBebidas: \n"
    for nome in bebidas_disponiveis:
        texto_opcoes += f"{nome} - R$ 12.99\n"
    texto_opcoes += "\n O que você deseja?"
    return texto_opcoes

def buscar_pedido():
    texto = "Este é o seu pedido: \n"
    texto += f"\nPizzas: {', '.join(pedido['pizzas'])}\n"
    texto += f"\nBebidas: {', '.join(pedido['bebidas'])}\n"
    texto += f"\nEndereço: {pedido['endereco']}\n"
    texto += f"\nValor: R${round(pedido['valor'],2)}"
    return texto

def solicitar_localizacao(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    botao_localizacao = types.KeyboardButton('Enviar Localização', request_location=True)
    markup.add(botao_localizacao)
    bot.send_message(message.chat.id, "Por favor, envie sua localização para entrega.", reply_markup=markup)

@bot.message_handler(commands=['start', 'restart'])
def iniciar_pedido(message):
    global pedido
    pedido = {
        "pizzas": [],
        "bebidas": [],
        "endereco": None,
        "valor": 0
    }
    bot.send_message(message.chat.id, "Olá! Bem-vindo ao Pizza Planet! Deseja pedir uma pizza?")
    texto = buscar_menu()
    bot.send_message(message.chat.id, texto)

@bot.message_handler(func=lambda message: True)
def responder_msg(message):
  if message.text:
    mensagem = message.text
    intencao = identificar_intencao(mensagem)
    if intencao == "pizza":
        pizza = identificar_pizza(mensagem)
        pedido["pizzas"].append(pizza)
        pedido["valor"] += pizzas_disponiveis[pizza]
        texto = f"Entendido, adicionei uma pizza de {pizza} no seu pedido"
        bot.send_message(message.chat.id, texto)
    elif intencao == "bebida":
        bebida = identificar_bebida(mensagem)
        pedido["bebidas"].append(bebida)
        pedido["valor"] += 12.99
        texto = f"Entendido, adicionei {bebida} no seu pedido"
        bot.send_message(message.chat.id, texto)
    elif intencao == "endereco":
        solicitar_localizacao(message)
    elif intencao == "cardapio":
      texto = buscar_menu()
      bot.send_message(message.chat.id, texto)
    elif intencao == "encerrar":
      if pedido["endereco"] != None:
        pedido_cliente = buscar_pedido()
        texto = f"Certo, seu pedido foi enviado para o preparo: \n{pedido_cliente}"
        texto += f"\nTempo de preparação: 30-40 minutos\nTempo de entrega: 20-30 minutos\n Obrigado e volte sempre!"
        bot.send_message(message.chat.id, texto)
      else:
        solicitar_localizacao(message)
  else:
    bot.send_message(message.chat.id, "Desculpe, não entendi seu pedido")

@bot.message_handler(content_types=['location'])
def receber_localizacao(message):
    if message.location is not None:
        latitude = message.location.latitude
        longitude = message.location.longitude
        location = geolocator.reverse(f"{latitude}, {longitude}", language="pt")
        endereco = location.raw['address']

        filtro = ['road', 'house_number', 'suburb', 'city', 'postcode']
        campos = [endereco.get(field, '') for field in filtro]

        endereco_reduzido = ', '.join(filter(None, campos))
        pedido["endereco"] = f"{endereco_reduzido}"
        texto = f"Recebi sua localização: {pedido['endereco']}"
        bot.send_message(message.chat.id, texto)

#bot.infinity_polling()
bot.polling()