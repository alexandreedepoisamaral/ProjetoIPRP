import turtle
import random
import time
import os
import sys

# =========================
# Parâmetros / Constantes
# =========================
LARGURA, ALTURA = 600, 900
BORDA_X = (LARGURA // 2) - 20
BORDA_Y = (ALTURA // 2) - 10

PLAYER_SPEED = 20
PLAYER_BULLET_SPEED = 16
ENEMY_SCORE= 100 # pontos por cada inimigo

ENEMY_ROWS = 3 
ENEMY_COLS = 10
ENEMY_SPACING_X = 60
ENEMY_SPACING_Y = 60 
ENEMY_SIZE = 32
ENEMY_START_Y = BORDA_Y - ENEMY_SIZE    # topo visível
ENEMY_FALL_SPEED = 0.5
ENEMY_DRIFT_STEP = 2
ENEMY_FIRE_PROB = 0.006
ENEMY_BULLET_SPEED = 8
ENEMY_INVERT_CHANCE = 0.05
ENEMY_DRIFT_CHANCE = 0.5

COLLISION_RADIUS = 10
HIGHSCORES_FILE = "highscores.txt"
SAVE_FILE = "savegame.txt"
TOP_N = 10

FILE_GUARDAR = "guardar_estado.txt"
FILE_CARREGAR = "carregar_estado.txt"

STATE = None  # usado apenas para callbacks do teclado

# =========================
# Top Resultados (Highscores)
# =========================
def ler_highscores(filename): #em implementação acho eu
    highscores = []
    if os.path.exists(filename): #verifica se existe
        with open (filename, 'r') as f: #abre em leitura
            for line in f:  
                line=line.strip() #remove espaços em brancos e quebras de linha
                if ',' in line: 
                     parts = line.split(',') #separa score e nome
                if len(parts) == 2:
                    score_str, name = parts
                if score_str.isdigit() or (score_str.startswith('-') and score_str[1:].isdigit()):
                    highscores.append((int(score_str), name))   
    f.close()
    highscores.sort(reverse=True)
    return highscores

def atualizar_highscores(filename, score):
    highscores = ler_highscores(filename)
    if score == 0:
        return 
    
    is_new_highscore = False
    # verifica se a lista não está cheia ou se a nova pontuação é maior que menor atual
    if len(highscores) < TOP_N or (highscores and score > highscores[-1][0]):  
         is_new_highscore = True
    if is_new_highscore:
        print(f"Novo highscore de {score}")
        name = input("Insira o seu nome: ").strip()
        highscores.append((score,name))
        highscores.sort(reverse=True)
        highscores = highscores[:TOP_N] # talvez adicionar : antes de top_n
        
        f = open(filename, 'w')
        for s, n in highscores: # itera sobre os scores e nomes
            f.write(f"{s},{n}\n") #formato score, nome 
        f.close()

# =========================
# Guardar / Carregar estado (texto)
# =========================
def guardar_estado_txt(filename, state): #verifica isto depois
    score = state["score"]
    frame = state["frame"]
    player = state["player"]
    player_x = player.xcor()
    player_y = player.ycor()
    enemies = state["enemies"]
    enemy_bullets = state["enemy_bullets"]
    player_bullets = state["player_bullets"]

    save_file = FILE_GUARDAR if filename == SAVE_FILE else filename
    if not os.path.exists(save_file):
        print("Ficheiro não encontrado")
        return False
    else:
        f = open(save_file, 'w ')
        f.write(f"score:{state['score']}\n")
        f.write(f"frame:{state["frame"]}\n")
        player = state["player"]
        f.write(f"player:{player.xcor()},{player.ycor()}\n")
        f.write("enemies:")
        for e, d in zip(state["enemies"], state["enemy_moves"]):
            f.write(f"{e.xcor()},{e.ycor()},{d['x']},{d['y']}|")
        f.write("\n")
        f.write("player_bullets:")
        for b in state["player_bullets"]:
            f.write(f"{b.xcor()}, {b.ycor()}|")
        f.write("\n")
        f.write("enemy_bullets:")
        for b in state["enemy_bullets"]:
            f.write(f"{b.xcor()},{b.ycor()}|")
        f.write("\n")
        f.close()
        print("Jogo guardado.")
        return True

def carregar_estado_txt(filename):
    if not filename:
        return {}
    if not os.path.exists(filename):
        print("Ficheiro não encontrado")
        return {}
    score = state["score"]
    frame = state["frame"]
    player = state["player"]
    player_x = player.xcor()
    player_y = player.ycor()
    enemies = state["enemies"]
    enemy_bullets = state["enemy_bullets"]
    player_bullets = state["player_bullets"]

# =========================
# Criação de entidades (jogador, inimigo e balas)
# =========================
def criar_entidade(x,y, tipo="enemy"):
    entidade = turtle.Turtle(visible=False)
    entidade.penup()
    entidade.speed(0)
    entidade.goto(x,y)

    if tipo == "player":
        entidade.shape("player.gif")
    else:
        entidade.shape("enemy.gif")
    
    entidade.showturtle()
    return entidade
def criar_bala(x, y, tipo):
    bala = turtle.Turtle(visible=False)
    bala.penup()
    bala.speed(0)
    bala.goto(x,y)
    
    if tipo == "player":
        bala.shape("circle")
        bala.color("white")
        bala.shapesize(stretch_len=0.5, stretch_wid=0.5)
        bala.setheading(90) 
    else:
        bala.shape("circle")
        bala.color("red")
        bala.shapesize(stretch_len=0.5, stretch_wid=0.5)
        bala.setheading(-90) 
    
    bala.showturtle()
    return bala

def spawn_inimigos_em_grelha(state, posicoes_existentes, dirs_existentes=None): #refazer isto melhor
    #limpa os atuais
    state["enemies"] = []
    state["enemy_moves"] =[]

    if posicoes_existentes and dirs_existentes: # se existem dados de carregamento
        #restaura os inimigos nas posições e movimentos salvos
        for (x,y), move in zip(posicoes_existentes, dirs_existentes):
            enemy = criar_entidade(x,y, "enemy")
            state["enemies"].append(enemy)
            state["enemy_moves"].append(move)
        return
    
    for row in range(ENEMY_ROWS): #nova grelha
        for col in range(ENEMY_COLS):
            x = ( col - ENEMY_COLS /2) * ENEMY_SPACING_X
            y = ENEMY_START_Y - row * ENEMY_SPACING_Y

            enemy = criar_entidade(x,y,"enemy")
            state["enemies"].append(enemy)
            #adaptar isto no fim
            initial_dir = random.choice([-ENEMY_DRIFT_STEP, ENEMY_DRIFT_STEP]) #escolhe direção inicial(-2 ou 2)
            state["enemy_moves"].append({"x": initial_dir, 'y': 0.0}) #adiciona vetor de movimento


def restaurar_balas(state, lista_pos, tipo):
    lista_balas = state[f"{tipo}_bullets"]

    for bala in lista_balas:
        bala.hideturtle() #esconde balas antigas

    lista_balas[:] = [] #limpa a lista de referencias ¿?

    for x,y in lista_pos:
        bala = criar_bala(x,y,tipo)
        lista_balas.append(bala)
# =========================
# Handlers de tecla 
# =========================
def mover_esquerda_handler():
    if STATE["player"] is None: return      

    p = STATE["player"]
    new_x = p.xcor() - PLAYER_SPEED
    if new_x < -BORDA_X: #limita o movimento à borda esquerda
        new_x = -BORDA_X
    p.setx(new_x) #aplica nova posição

def mover_direita_handler():
    if STATE["player"] is None: return
    
    p = STATE["player"]
    new_x = p.xcor() + PLAYER_SPEED
    
    if new_x > BORDA_X:
        new_x = BORDA_X
    p.setx(new_x)

def disparar_handler():
    if STATE["player"] is None: return
    
    if len(STATE["player_bullets"]) < 10: #trocar para o metodo do joao
        p = STATE["player"]
        bala = criar_bala(p.xcor(), p.ycor() - 10, "player")
        STATE["player_bullets"].append(bala)

def gravar_handler():
    guardar_estado_txt(STATE["files"]["save"], STATE)

def terminar_handler():
    print("FIM DE JOGO")
    if STATE.get("player"): STATE["player"].hideturtle()
    for e in STATE["enemies"]: e.hideturtle()
    for b in STATE["player_bullets"]: b.hideturtle()
    for b in STATE["enemy_bullets"]: b.hideturtle()
    
    atualizar_highscores(STATE["files"]["highscores"], STATE["score"])
    time.sleep(1)
    sys.exit(0)

# =========================
# Atualizações e colisões
# =========================
def atualizar_balas_player(state):
    for bala in STATE["player_bullets"]:
        new_y = bala.ycor() + PLAYER_BULLET_SPEED
        bala.sety(new_y)
        if new_y > BORDA_Y:
            bala.hideturtle()
            STATE["player_bullets"].remove(bala)
def atualizar_balas_inimigos(state):
    for bala in STATE["enemy_bullets"]:
        new_y = bala.ycor() - ENEMY_BULLET_SPEED
        bala.sety(new_y)
        if new_y > BORDA_Y:
            bala.hideturtle()
            STATE["enemy_bullets"]
def atualizar_inimigos(state):
    for enemies in STATE["enemies"]:
        new_y = enemies.ycor() - ENEMY_FALL_SPEED 
        enemies.sety(new_y)
        if new_y < -BORDA_Y:
            enemies.hideturtle()
            STATE["enemies"].remove(enemies)
        new_x = enemies.xcor() + random.choice([-ENEMY_DRIFT_STEP, ENEMY_DRIFT_STEP]) #nao funciona
        if new_x < -BORDA_X:
            new_x = enemies.xcor()
            enemies.setx(new_x)

def inimigos_disparam(state):
    for enemy in STATE["enemies"]:
        if random.random() < ENEMY_FIRE_PROB:
            x = enemy.xcor()
            y = enemy.ycor() - 20
            bala = criar_bala(x,y,"enemy")
            STATE["enemy_bullets"].append(bala)

def verificar_colisoes_player_bullets(state):
    if not STATE["player_bullets"]: 
        return False
    else:
        for bullet in STATE["player_bullets"]:
            for enemy in STATE["enemies"]:
                if bullet.distance(enemy) < COLLISION_RADIUS:
                    bullet.hideturtle()
                    enemy.hideturtle()
                    STATE["player_bullets"].remove(bullet)
                    STATE["enemies"].remove(enemy)
                    STATE["score"] += ENEMY_SCORE
        return True
def verificar_colisoes_enemy_bullets(state):
    if STATE["enemy_bullets"] == []:
        return False
    else: 
        player = STATE["player"]
        for bullet in STATE["enemy_bullets"]:
            if player and bullet.distance(player) < COLLISION_RADIUS:
                bullet.hideturtle()
                STATE["enemy_bullets"].remove(bullet)
                player.hideturtle()
                STATE["player"] = None # jogador destruido
                return True  # houve colisao
        return False         # nao houve colisao
def inimigo_chegou_ao_fundo(state):
    if STATE["player"] is None: return False
    player_y = state["player"].ycor()
    for enemy in state["enemies"]:
        if enemy.ycor() <= player_y:
            return True
    return False

def verificar_colisao_player_com_inimigos(state): #refaz isto mais simples depois secalhar
    player = state["player"]
    if player is None: #se ja morreu
        return False
    max_dist = COLLISION_RADIUS
    for enemy in state["enemies"]:
        distancia = player.distance(enemy)
        if distancia < max_dist:
            player.hideturtle()
            state["player"] = None
            return True
    return False

# =========================
# Execução principal
# =========================
if __name__ == "__main__":
    # Pergunta inicial: carregar?
    filename = input("Carregar jogo? Se sim, escreva nome do ficheiro, senão carregue Return: ").strip()
    loaded = carregar_estado_txt(filename)

    # Ecrã
    screen = turtle.Screen()
    screen.title("Space Invaders IPRP")
    screen.bgcolor("black")
    screen.setup(width=LARGURA, height=ALTURA)
    screen.tracer(0)

    # Imagens obrigatórias
    for img in ["player.gif", "enemy.gif"]:
        if not os.path.exists(img):
            print("ERRO: imagem '" + img + "' não encontrada.")
            sys.exit(1)
        screen.addshape(img)

    # Estado base
    state = {
        "screen": screen,
        "player": None, 
        "enemies": [],
        "enemy_moves": [],          
        "player_bullets": [],
        "enemy_bullets": [],
        "score": 0,
        "frame": 0,
        "files": {"highscores": HIGHSCORES_FILE, "save": SAVE_FILE}
    }

    # Construção inicial
    if loaded: #reset
        state["score"]= loaded.get["score",0]
        state["frame"]= loaded.get["frame",0]
        px, py = loaded.get("player_pos", (0, -350)) 
        state["player"] = criar_entidade(px,py,"player")
        spawn_inimigos_em_grelha(state,loaded.get("enemies"), loaded.get("enemy_moves"))
    else:
        print("New game!")
        state["player"] = criar_entidade(0, -350,"player")
        spawn_inimigos_em_grelha(state, None)

    # Variavel global para os keyboard key handlers
    STATE = state

    # Teclas
    screen.listen()
    screen.onkeypress(mover_esquerda_handler, "Left")
    screen.onkeypress(mover_direita_handler, "Right")
    screen.onkeypress(disparar_handler, "space")
    screen.onkeypress(gravar_handler, "g")
    screen.onkeypress(terminar_handler, "Escape")

    # Loop principal
    while True:
        atualizar_balas_player(STATE)
        atualizar_inimigos(STATE)
        inimigos_disparam(STATE)
        atualizar_balas_inimigos(STATE)
        verificar_colisoes_player_bullets(STATE)
        
        if verificar_colisao_player_com_inimigos(STATE):
            print("Colisão direta com inimigo! Game Over")
            terminar_handler()
        
        if verificar_colisoes_enemy_bullets(STATE):
            print("Atingido por inimigo! Game Over")
            terminar_handler()

        if inimigo_chegou_ao_fundo(STATE):
            print("Um inimigo chegou ao fundo! Game Over")
            terminar_handler()

        if len(STATE["enemies"]) == 0:
            print("Vitória! Todos os inimigos foram destruídos.")
            terminar_handler()

        STATE["frame"] += 1
        screen.update()
        time.sleep(0.016)

def minhafuncaosoma(a,b):
    return a+b  
