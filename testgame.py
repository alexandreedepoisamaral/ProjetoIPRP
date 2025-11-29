import turtle 
import random # Importa o módulo random para gerar números aleatórios
import time # Importa o módulo time para funções relacionadas com tempo (pausas)
import os # Importa o módulo os para interagir com o sistema operativo (ficheiros)
import sys # Importa o módulo sys para interagir com o interpretador Python (sair do programa)

# =========================
# Parâmetros / Constantes
# =========================
LARGURA, ALTURA = 600, 900 # Define a largura e altura da janela de jogo
BORDA_X = (LARGURA // 2) - 20 # Calcula o limite horizontal para o movimento das entidades
BORDA_Y = (ALTURA // 2) - 10 # Calcula o limite vertical para o movimento das entidades

PLAYER_SPEED = 20 # Define a velocidade de movimento horizontal do jogador
PLAYER_BULLET_SPEED = 16 # Define a velocidade vertical das balas do jogador
ENEMY_SCORE = 100 # Define a pontuação ganha por destruir um inimigo

ENEMY_ROWS = 3 # Define o número de linhas de inimigos
ENEMY_COLS = 10 # Define o número de colunas de inimigos
ENEMY_SPACING_X = 60 # Define o espaçamento horizontal entre inimigos
ENEMY_SPACING_Y = 60 # Define o espaçamento vertical entre inimigos
ENEMY_SIZE = 32 # Define o tamanho visual de referência do inimigo
ENEMY_START_Y = BORDA_Y - ENEMY_SIZE# Define a posição Y inicial para a primeira linha de inimigos
ENEMY_FALL_SPEED = 0.5 # Define a velocidade inicial de queda após atingir a borda
ENEMY_DRIFT_STEP = 2 # Define a velocidade de movimento lateral (drift) dos inimigos
ENEMY_FIRE_PROB = 0.006 # Define a probabilidade de um inimigo disparar por frame
ENEMY_BULLET_SPEED = 8 # Define a velocidade vertical das balas dos inimigos

COLLISION_RADIUS = 15 # Define o raio usado para detetar colisões
HIGHSCORES_FILE = "highscores.txt" # Define o nome do ficheiro de pontuações máximas
SAVE_FILE = "savegame.txt" # Define o nome do ficheiro de gravação (nome lógico para o handler)
TOP_N = 10 # Define o número máximo de highscores a guardar

FILE_GUARDAR = "guardar_estado.txt" # Nome real do ficheiro de gravação usado internamente
FILE_CARREGAR = "carregar_estado.txt" # Nome real do ficheiro de carregamento usado internamente (padrão)

STATE = None # Variável global que irá armazenar o estado completo do jogo

# =========================
# Top Resultados (Highscores)
# =========================
def ler_highscores(filename):
    highscores = [] # Inicializa a lista de highscores (tuplos de (pontuação, nome))
    if os.path.exists(filename): # Verifica se o ficheiro de highscores existe
        f = open(filename, 'r') # Abre o ficheiro em modo de leitura
        for line in f: # Itera sobre cada linha do ficheiro
            line = line.strip() # Remove espaços em branco e nova linha
            if ',' in line: # Verifica se a linha está formatada com o separador vírgula
                parts = line.split(',') # Divide a linha em partes (score e name)
                if len(parts) == 2: # Garante que existem exatamente duas partes
                    score_str, name = parts
                    # Valida se a string do score é um inteiro (positivo ou negativo) sem usar try
                    if score_str.isdigit() or (score_str.startswith('-') and score_str[1:].isdigit()):
                        highscores.append((int(score_str), name)) # Adiciona o tuplo convertido
        f.close() # Fecha o ficheiro após a leitura
    
    highscores.sort(key=lambda x: x[0], reverse=True) # Ordena a lista pela pontuação (x[0]) em ordem decrescente (do maior para o menor)
    return highscores[:TOP_N] # Retorna apenas o número máximo de highscores definidos

def atualizar_highscores(filename, score):
    highscores = ler_highscores(filename) # Carrega os highscores atuais

    if score == 0: # Se a pontuação for zero, não faz nada
        return

    is_new_highscore = False # Flag para verificar se a pontuação é nova
    # Verifica se há espaço OU se a pontuação é maior que a menor pontuação atual (highscores[-1][0])
    if len(highscores) < TOP_N or (highscores and score > highscores[-1][0]):
        is_new_highscore = True

    if is_new_highscore: # Se for um novo highscore
        print(f"Novo Highscore! A sua pontuação: {score}")
        name = input("Insira o seu nome: ").strip() or "ANON" # Pede o nome ao utilizador, usando "ANON" se for vazio
        highscores.append((score, name)) # Adiciona a nova pontuação e nome à lista
        highscores.sort(key=lambda x: x[0], reverse=True) # Reordena a lista novamente
        highscores = highscores[:TOP_N] # Trunca a lista para manter apenas o TOP N

        f = open(filename, 'w') # Abre o ficheiro em modo de escrita (sobrescreve o conteúdo existente)
        for s, n in highscores: # Itera sobre os highscores ordenados
            f.write(f"{s},{n}\n") # Escreve cada highscore no formato "score,nome" e adiciona uma quebra de linha
        f.close() # Fecha o ficheiro
        print("Highscores atualizados.")

# =========================
# Guardar / Carregar estado (texto)
# =========================
def guardar_estado_txt(filename, state):
    # Escolhe o nome do ficheiro para guardar (uso interno ou nome fornecido)
    save_file = FILE_GUARDAR if filename == SAVE_FILE else filename
    print(f"Guardando estado em {save_file}...")
    
    f = open(save_file, 'w') # Abre o ficheiro para escrita
    # 1. Score e Frame 
    f.write(f"score:{state['score']}\n") # Escreve a pontuação atual
    f.write(f"frame:{state['frame']}\n") # Escreve o número do frame atual
    
    # 2. Player (posição X e Y)
    p = state["player"]
    f.write(f"player:{p.xcor()},{p.ycor()}\n") # Escreve as coordenadas atuais do jogador
    
    # 3. Inimigos (posição X, Y e vetor de movimento X, Y)
    f.write("enemies:")
    for e, d in zip(state["enemies"], state["enemy_moves"]): # Itera sobre inimigos e movimentos simultaneamente
        f.write(f"{e.xcor()},{e.ycor()},{d['x']},{d['y']}|") # Escreve posições e vetores, separados por '|'
    f.write("\n")

    # 4. Balas do Jogador (posição X e Y)
    f.write("player_bullets:")
    for b in state["player_bullets"]:
        f.write(f"{b.xcor()},{b.ycor()}|")
    f.write("\n")

    # 5. Balas do Inimigo (posição X e Y)
    f.write("enemy_bullets:")
    for b in state["enemy_bullets"]:
        f.write(f"{b.xcor()},{b.ycor()}|")
    f.write("\n")
    
    f.close() # Fecha o ficheiro
    print("Jogo guardado com sucesso.")

def carregar_estado_txt(filename):
    # Função aninhada para converter string para float de forma segura (sem usar try/except)
    def string_para_float_seguro(s):
        s = str(s).strip() # Converte para string e remove espaços
        if not s: # Se a string estiver vazia, retorna None (inválida)
            return None
        
        is_negative = s.startswith('-') # Verifica se tem sinal negativo
        if is_negative:
            s = s[1:] # Remove o sinal para validar o resto da string
            
        if s.count('.') > 1: # Se tiver mais de um ponto decimal, é inválido
            return None 
            
        parts = s.split('.') # Divide a string nas partes inteira e decimal
        
        # Verifica se as partes (inteira e decimal) contêm apenas dígitos (ou se estão vazias, como em ".5" ou "5.")
        for part in parts:
            if part and not part.isdigit():
                return None # Se encontrar um caractere não dígito, é inválido
        
        if s == '.': # Se a string for apenas um ponto, é inválido
            return None

        # Se passou na validação, converte para float
        return float("-" + s) if is_negative else float(s)

    # Escolhe o nome do ficheiro para carregar
    load_file = FILE_CARREGAR if not filename else filename
    
    if not os.path.exists(load_file): # Verifica se o ficheiro existe
        if filename: 
            print(f"Ficheiro de gravação '{filename}' não encontrado.")
        return None
        
    print(f"Tentando carregar estado de {load_file}...")
    
    f = open(load_file, 'r') # Abre o ficheiro para leitura
    lines = f.readlines() # Lê todas as linhas
    f.close() # Fecha o ficheiro
    
    data = {"enemies": [], "enemy_moves": []} # Dicionário para armazenar dados carregados
    
    for line in lines: # Itera sobre cada linha lida
        line = line.strip()
        
        # 1. Score e Frame
        if line.startswith("score:"):
            score_str = line[6:]
            if score_str.isdigit(): # Valida se é um número inteiro positivo
                data["score"] = int(score_str)
        elif line.startswith("frame:"):
            frame_str = line[6:]
            if frame_str.isdigit(): # Valida se é um número inteiro positivo
                data["frame"] = int(frame_str)
        
        # 2. Player
        elif line.startswith("player:"):
            parts = line[7:].split(',')
            if len(parts) == 2:
                x = string_para_float_seguro(parts[0]) # Converte X com validação manual
                y = string_para_float_seguro(parts[1]) # Converte Y com validação manual
                if x is not None and y is not None: # Se as conversões forem válidas
                    data["player_pos"] = (x, y)
        
        # 3. Inimigos
        elif line.startswith("enemies:"):
            enemy_data = line[8:].split('|')
            for d in enemy_data: # Itera sobre cada inimigo serializado
                if d:
                    parts = d.split(',')
                    if len(parts) == 4: # Espera 4 valores (Ex, Ey, Dx, Dy)
                        ex = string_para_float_seguro(parts[0])
                        ey = string_para_float_seguro(parts[1])
                        dx = string_para_float_seguro(parts[2])
                        dy = string_para_float_seguro(parts[3])
                        
                        if ex is not None and ey is not None and dx is not None and dy is not None:
                            data["enemies"].append((ex, ey)) # Adiciona a posição do inimigo
                            data["enemy_moves"].append({'x': dx, 'y': dy}) # Adiciona o vetor de movimento
                            
        # 4. Balas do Jogador
        elif line.startswith("player_bullets:"):
            bullet_data = line[15:].split('|')
            data["player_bullets"] = []
            for b in bullet_data:
                if b and ',' in b:
                    parts = b.split(',')
                    if len(parts) == 2:
                        bx = string_para_float_seguro(parts[0])
                        by = string_para_float_seguro(parts[1])
                        if bx is not None and by is not None:
                            data["player_bullets"].append((bx, by)) # Adiciona a posição da bala

        # 5. Balas do Inimigo
        elif line.startswith("enemy_bullets:"):
            bullet_data = line[14:].split('|')
            data["enemy_bullets"] = []
            for b in bullet_data:
                if b and ',' in b:
                    parts = b.split(',')
                    if len(parts) == 2:
                        bx = string_para_float_seguro(parts[0])
                        by = string_para_float_seguro(parts[1])
                        if bx is not None and by is not None:
                            data["enemy_bullets"].append((bx, by))
    
    # Verifica se os dados essenciais (score e posição do player) foram carregados com sucesso
    if "score" in data and "player_pos" in data:
        return data # Retorna o dicionário de dados puros
    else:
        print("Ficheiro de gravação incompleto ou corrompido.")
        return None

# =========================
# Criação de entidades (jogador, inimigo e balas)
# =========================
def criar_entidade(x,y, tipo="enemy"):
    t = turtle.Turtle(visible=False) # Cria um novo objeto Turtle (invisível por padrão)
    t.penup() # Levanta a caneta (não desenha ao mover)
    t.speed(0) # Define a velocidade máxima de animação (sem delay)
    t.goto(x, y) # Move a entidade para as coordenadas iniciais
    
    if tipo == "player": # Se for o jogador
        t.shape("player.gif") # Usa a imagem do jogador
    else: # Se for um inimigo
        t.shape("enemy.gif") # Usa a imagem do inimigo
    
    t.showturtle() # Torna a entidade visível
    return t

def criar_bala(x, y, tipo):
    t = turtle.Turtle(visible=False) # Cria um novo objeto Turtle para a bala
    t.penup()
    t.speed(0)
    t.goto(x, y)
    
    if tipo == "player": # Se for bala do jogador
        t.shape("circle") # Define o formato como círculo
        t.color("white") # Define a cor branca
        t.shapesize(stretch_len=0.5, stretch_wid=0.5) # Reduz o tamanho da forma
        t.setheading(90) # Define a direção para cima
    else: # Se for bala do inimigo
        t.shape("square") # Define o formato como quadrado
        t.color("red") # Define a cor vermelha
        t.shapesize(stretch_len=0.5, stretch_wid=0.5)
        t.setheading(270) # Define a direção para baixo
    
    t.showturtle()
    return t

def spawn_inimigos_em_grelha(state, posicoes_existentes, dirs_existentes=None):
    state["enemies"] = [] # Limpa a lista de objetos inimigos atuais
    state["enemy_moves"] = [] # Limpa a lista de vetores de movimento atuais

    if posicoes_existentes and dirs_existentes: # Se existem dados de carregamento
        # Restaura os inimigos nas posições e movimentos salvos
        for (x, y), move in zip(posicoes_existentes, dirs_existentes):
            enemy = criar_entidade(x, y, "enemy")
            state["enemies"].append(enemy)
            state["enemy_moves"].append(move) 
        return

    # Criação de uma nova grelha
    for row in range(ENEMY_ROWS): # Itera sobre o número de linhas
        for col in range(ENEMY_COLS): # Itera sobre o número de colunas
            # Calcula a posição X para centrar a grelha
            x = (col - ENEMY_COLS / 2) * ENEMY_SPACING_X + ENEMY_SPACING_X / 2
            # Calcula a posição Y (começa no topo e desce)
            y = ENEMY_START_Y - (row * ENEMY_SPACING_Y)
            
            enemy = criar_entidade(x, y, "enemy")
            state["enemies"].append(enemy)
            
            initial_dir = random.choice([-ENEMY_DRIFT_STEP, ENEMY_DRIFT_STEP]) # Escolhe direção inicial (-2 ou 2)
            state["enemy_moves"].append({'x': initial_dir, 'y': 0.0}) # Adiciona o vetor de movimento (sem queda inicial)

def restaurar_balas(state, lista_pos, tipo):
    lista_balas = state[f"{tipo}_bullets"]
    
    for bala in lista_balas: # Esconde as balas antigas
        bala.hideturtle()
    
    lista_balas[:] = [] # Limpa a lista de referências (in-place)
    
    for x, y in lista_pos: # Itera sobre as posições carregadas
        bala = criar_bala(x, y, tipo) # Cria o novo objeto bala
        lista_balas.append(bala) # Adiciona à lista

# =========================
# Handlers de tecla 
# =========================
def mover_esquerda_handler():
    if STATE["player"] is None: return # Sai se o jogador não existir
    
    p = STATE["player"]
    new_x = p.xcor() - PLAYER_SPEED # Calcula a nova posição X para a esquerda
    
    if new_x < -BORDA_X: # Limita o movimento à borda esquerda
        new_x = -BORDA_X
        
    p.setx(new_x) # Aplica a nova posição

def mover_direita_handler():
    if STATE["player"] is None: return
        
    p = STATE["player"]
    new_x = p.xcor() + PLAYER_SPEED # Calcula a nova posição X para a direita
    
    if new_x > BORDA_X: # Limita o movimento à borda direita
        new_x = BORDA_X
        
    p.setx(new_x)

def disparar_handler():
    if STATE["player"] is None: return
    
    if len(STATE["player_bullets"]) < 5: # Verifica o limite de balas ativas (5)
        p = STATE["player"]
        bala = criar_bala(p.xcor(), p.ycor() + 20, "player") # Cria a bala
        STATE["player_bullets"].append(bala)

def gravar_handler():
    # Chama a função de guardar, passando o nome do ficheiro de gravação padrão
    guardar_estado_txt(STATE["files"]["save"], STATE)

def terminar_handler():
    print("-------------------------")
    print("FIM DE JOGO.")
    print(f"Pontuação Final: {STATE['score']}")
    print("-------------------------")
    
    # Esconde todas as entidades visíveis
    if STATE.get("player"): STATE["player"].hideturtle()
    for e in STATE["enemies"]: e.hideturtle()
    for b in STATE["player_bullets"]: b.hideturtle()
    for b in STATE["enemy_bullets"]: b.hideturtle()
    
    atualizar_highscores(STATE["files"]["highscores"], STATE["score"]) # Grava pontuação máxima
    time.sleep(1) # Pequena pausa
    sys.exit(0) # Termina o programa

# =========================
# Atualizações e colisões
# =========================
def atualizar_balas_player(state):
    balas_ativas = [] # Lista temporária para balas que permanecem no ecrã
    for bala in state["player_bullets"]:
        bala.sety(bala.ycor() + PLAYER_BULLET_SPEED) # Move a bala para cima
        
        if bala.ycor() < BORDA_Y: # Se a bala ainda estiver dentro do limite superior
            balas_ativas.append(bala)
        else:
            bala.hideturtle() # Esconde a bala se saiu do ecrã
    
    state["player_bullets"] = balas_ativas # Atualiza a lista principal

def atualizar_balas_inimigos(state):
    balas_ativas = []
    for bala in state["enemy_bullets"]:
        bala.sety(bala.ycor() - ENEMY_BULLET_SPEED) # Move a bala para baixo
        
        if bala.ycor() > -BORDA_Y: # Se a bala ainda estiver dentro do limite inferior
            balas_ativas.append(bala)
        else:
            bala.hideturtle()
    
    state["enemy_bullets"] = balas_ativas

def atualizar_inimigos(state):
    all_enemies = list(zip(state["enemies"], state["enemy_moves"])) # Combina inimigo e vetor de movimento
    boundary_hit = False # Flag para colisão com a borda
    
    for enemy, move in all_enemies:
        enemy.setx(enemy.xcor() + move['x']) # Aplica o movimento horizontal
        
        if enemy.xcor() > BORDA_X or enemy.xcor() < -BORDA_X: # Verifica colisão com bordas laterais
            boundary_hit = True
            
            # Corrige a posição para garantir que fica dentro do limite
            if enemy.xcor() > BORDA_X:
                enemy.setx(BORDA_X)
            else:
                enemy.setx(-BORDA_X)

    if boundary_hit: # Se houve colisão com a borda, todos os inimigos reagem
        for move in state["enemy_moves"]:
            move['x'] *= -1 # Inverte a direção horizontal
            move['y'] += ENEMY_FALL_SPEED # Aumenta a velocidade de queda

    for enemy, move in all_enemies:
        if move['y'] > 0: # Aplica a queda vertical, se houver
            enemy.sety(enemy.ycor() - move['y'])

def inimigos_disparam(state):
    if not state["enemies"]: # Se não houver inimigos, sai
        return

    if random.random() < ENEMY_FIRE_PROB: # Verifica a probabilidade de disparo
        shooter = random.choice(state["enemies"]) # Escolhe um inimigo aleatório
        
        bala = criar_bala(shooter.xcor(), shooter.ycor() - 20, "enemy")
        state["enemy_bullets"].append(bala)

def verificar_colisoes_player_bullets(state):
    balas_ativas = []
    
    inimigos_a_remover_indices = []

    for bala in state["player_bullets"]: # Itera sobre cada bala do jogador
        atingiu_inimigo = False
        
        for i, enemy in enumerate(state["enemies"]): # Itera sobre cada inimigo com índice
            # Fórmula da distância quadrada
            dist_sq = (bala.xcor() - enemy.xcor())**2 + (bala.ycor() - enemy.ycor())**2
            if dist_sq < (COLLISION_RADIUS * COLLISION_RADIUS): # Colisão detetada
                atingiu_inimigo = True
                
                inimigos_a_remover_indices.append(i) # Marca o índice para remoção
                
                state["score"] += ENEMY_SCORE # Aumenta a pontuação
                bala.hideturtle() # Esconde a bala
                break # Sai do loop de inimigos, pois a bala já atingiu um
        
        if not atingiu_inimigo:
            balas_ativas.append(bala) # Mantém a bala se não colidiu

    inimigos_a_remover_indices.sort(reverse=True) # Ordena os índices do maior para o menor
    
    for index in inimigos_a_remover_indices: # Itera sobre os índices a remover
        state["enemies"][index].hideturtle() # Esconde o objeto Turtle
        state["enemies"].pop(index) # Remove o objeto inimigo da lista
        state["enemy_moves"].pop(index) # Remove o vetor de movimento correspondente

    state["player_bullets"] = balas_ativas
    
    if len(state["enemies"]) == 0:
        return True # Nível limpo
    return False

def verificar_colisoes_enemy_bullets(state):
    balas_ativas = []
    colisao_com_player = False
    player = state["player"]

    for bala in state["enemy_bullets"]:
        # Colisão entre bala inimiga e jogador
        dist_sq = (bala.xcor() - player.xcor())**2 + (bala.ycor() - player.ycor())**2
        
        if dist_sq < (COLLISION_RADIUS * COLLISION_RADIUS):
            colisao_com_player = True # Colisão com o jogador
            bala.hideturtle()
        else:
            balas_ativas.append(bala)

    state["enemy_bullets"] = balas_ativas
    return colisao_com_player

def inimigo_chegou_ao_fundo(state):
    player_y = state["player"].ycor()
    
    for enemy in state["enemies"]:
        if enemy.ycor() == player_y + 20: # Se o inimigo desceu até a proximidade do jogador
            return True
            
    return False

def verificar_colisao_player_com_inimigos(state):
    player = state["player"]
    for enemy in state["enemies"]:
        # Colisão direta entre inimigo e jogador (usa um raio de colisão maior)
        dist_sq = (player.xcor() - enemy.xcor())**2 + (player.ycor() - enemy.ycor())**2
        if dist_sq < (COLLISION_RADIUS * 2 * COLLISION_RADIUS * 2): 
            return True
    return False

# =========================
# Execução principal
# =========================
if __name__ == "__main__":
    # Pede ao utilizador para carregar um jogo ou iniciar um novo
    filename = input("Carregar jogo? Se sim, escreva nome do ficheiro, senão carregue Return (irá tentar 'carregar_estado.txt'): ").strip()
    loaded_data = carregar_estado_txt(filename) # Tenta carregar o estado

    # Configuração da janela (Screen)
    screen = turtle.Screen()
    screen.title("Space Invaders IPRP")
    screen.bgcolor("black")
    screen.setup(width=LARGURA, height=ALTURA) # Define o tamanho da janela
    screen.tracer(0) # Desliga a atualização automática (controlada por screen.update())

    # Carregamento de Imagens
    for img in ["player.gif", "enemy.gif"]: # Lista de imagens obrigatórias
        if not os.path.exists(img): # Verifica se o ficheiro existe
            print("ERRO: imagem '" + img + "' não encontrada.")
            sys.exit(1) # Termina o programa com erro
        screen.addshape(img) # Adiciona a imagem ao Turtle

    # Estado base inicial
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

    # Lógica de Novo Jogo ou Carregamento
    if loaded_data:
        print("Jogo carregado.")
        state["score"] = loaded_data.get("score", 0) # Restaura a pontuação
        state["frame"] = loaded_data.get("frame", 0) # Restaura o frame
        
        px, py = loaded_data["player_pos"]
        state["player"] = criar_entidade(px, py,"player") # Cria o jogador na posição salva
        
        spawn_inimigos_em_grelha(state, loaded_data.get("enemies"), loaded_data.get("enemy_moves")) # Restaura inimigos
        
        restaurar_balas(state, loaded_data.get("player_bullets", []), "player") # Restaura balas do jogador
        restaurar_balas(state, loaded_data.get("enemy_bullets", []), "enemy") # Restaura balas do inimigo
        
    else:
        print("New game!")
        state["player"] = criar_entidade(0, -350,"player") # Cria o jogador na posição inicial
        spawn_inimigos_em_grelha(state, None, None) # Cria a grelha inicial de inimigos

    # Atribui o estado inicial à variável global
    STATE = state

    # Configuração de Teclas (event handlers)
    screen.listen() # Começa a escutar eventos de teclado
    screen.onkeypress(mover_esquerda_handler, "Left") # Mover esquerda
    screen.onkeypress(mover_direita_handler, "Right") # Mover direita
    screen.onkeypress(disparar_handler, "space") # Disparar
    screen.onkeypress(gravar_handler, "g") # Gravar estado
    screen.onkeypress(terminar_handler, "Escape") # Terminar jogo

    # Loop principal do jogo
    while True:
        # FASE 1: Atualizações de Movimento
        atualizar_balas_player(STATE)
        atualizar_inimigos(STATE)
        inimigos_disparam(STATE)
        atualizar_balas_inimigos(STATE)
        
        # FASE 2: Verificação de Colisões (Balas do Jogador)
        nivel_limpo = verificar_colisoes_player_bullets(STATE)
        
        # FASE 3: Condições de Fim de Jogo
        if verificar_colisao_player_com_inimigos(STATE): # Colisão direta
            print("Colisão direta com inimigo! Game Over")
            terminar_handler()
        
        if verificar_colisoes_enemy_bullets(STATE): # Colisão com bala inimiga
            print("Atingido por inimigo! Game Over")
            terminar_handler()

        if inimigo_chegou_ao_fundo(STATE): # Inimigo atingiu a linha do jogador
            print("Um inimigo chegou ao fundo! Game Over")
            terminar_handler()

        if nivel_limpo: # Se todos os inimigos foram destruídos
            print("Vitória! Inimigos destruídos. Próximo nível...")
            spawn_inimigos_em_grelha(STATE, None, None) # Spawna uma nova onda

        STATE["frame"] += 1 # Incrementa o contador de frames
        screen.update() # Força a redesenhar o ecrã
        time.sleep(0.016) # Pausa o loop para controlar a velocidade (aprox. 60 FPS)