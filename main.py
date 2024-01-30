import time

class PlayerData:
    def __init__(
        self,
        id,
        name_short,
        name_long,
        positions,
        nationality,
        club,
        league,
        ratings=None,
        tags=None
    ):
        self.id = id
        self.name_short = name_short
        self.name_long = name_long
        self.positions = positions or []
        self.nationality = nationality
        self.club = club
        self.league = league
        self.ratings = ratings or []
        self.rating_count = len(ratings) if ratings else 0
        self.rating = (
            sum(rating for rating in ratings) / len(ratings)
            if ratings
            else 0.0
        )
        self.user_ratings = {}  # Adiciona o atributo user_ratings
        self.tags = tags or []  # Adiciona o atributo tags

class Node:
    def __init__(self, prefix):
        self.prefix = prefix
        self.children = []

    def add_child(self, id):
        self.children.append(id)

    def get_children_with_prefix(self, prefix):
        children = []
        for child in self.children:
            if child.prefix.startswith(prefix):
                children.append(child)
        return children
            
def finditer(pattern, s):
    matches = []
    pos = 0
    while True:
        m = pattern.match(s, pos)
        if m is None:
            break

        matches.append(m)
        pos = m.end()

    return matches


def read_csv(filename):
    with open(filename, "r") as f:
        reader = f.readlines()

    records = []
    for line in reader:
        records.append(_process_line(line))

    return iter(records)


def read_csv(filename):
    with open(filename, "r") as f:
        for line in f:
            yield _process_line(line)

def _process_line(line):
    columns = []
    line = line.strip("\n")

    quoted_columns = line.split(',"')
    if len(quoted_columns) == 2:
        columns = quoted_columns[0].split(",") + [quoted_columns[1].split('",')[0]] + quoted_columns[1].split('",')[1].split(",")
    else:
        columns = line.split(",")

    return columns



def build_prefix_tree(players_csv):
    prefix_tree = {}

    with open(players_csv, "r") as f:
        reader = read_csv(players_csv)
        next(reader, None)  # Skip header

        for row in reader:
            name_long = row[2]

            for i in range(len(name_long)):
                prefix = name_long[:i + 1]

                if prefix not in prefix_tree:
                    prefix_tree[prefix] = Node(prefix)

                prefix_tree[prefix].add_child(row[0])

    return prefix_tree


def build_player_data_hash(players_csv, ratings_csv, tags_csv):
    start_time_total = time.perf_counter()

    player_data_hash = {}

    # Lê o arquivo players.csv
    start_time_players = time.perf_counter()

    with open(players_csv, "r") as f:
        reader = read_csv(players_csv)
        next(reader, None)  # Skip header

        for row in reader:
            #print(f"{row}")
            if len(row) == 7 and not player_data_hash.get(str(row[0])):
                id, name_short, name_long, positions, nationality, club, league = row

                player_data = PlayerData(
                    id=int(id),
                    name_short=name_short,
                    name_long=name_long,
                    positions=positions.split(","),
                    nationality=nationality,
                    club=club,
                    league=league,
                )

                player_data_hash[id] = player_data

    end_time_players = time.perf_counter()
    print(f"Tempo de carregamento de players.csv: {end_time_players - start_time_players:.2f} segundos")

    # Lê o arquivo ratings.csv
    start_time_ratings = time.perf_counter()

    with open(ratings_csv, "r") as r:
        reader_r = read_csv(ratings_csv)
        next(reader_r, None)  # Skip header

        for row_r in reader_r:
            player_id = str(row_r[1])
            if player_data_hash.get(player_id):
                rating = float(row_r[2])
                username = str(row_r[0])  # Adiciona o username

                # Atribui o rating ao dicionário user_ratings
                player_data_hash[player_id].user_ratings[username] = rating

                # Atualiza o rating global também, caso necessário
                player_data_hash[player_id].ratings.append(rating)

        # Calcula o rating global para todos os jogadores
        for player_data in player_data_hash.values():
            player_data.rating_count = len(player_data.ratings)
            player_data.rating = (
                sum(player_data.ratings) / player_data.rating_count
            ) if player_data.rating_count > 0 else 0
                
    end_time_ratings = time.perf_counter()
    print(f"Tempo de carregamento de ratings.csv: {end_time_ratings - start_time_ratings:.2f} segundos")

    # Lê o arquivo tags.csv
    start_time_tags = time.perf_counter()

    with open(tags_csv, "r") as t:
        reader_t = read_csv(tags_csv)
        next(reader_t, None)  # Skip header

        for row_t in reader_t:
            if player_data_hash.get(str(row_r[1])):
                player_data_hash[str(row_r[1])].tags.append(str(row_t[2]))
                #print(f"{player_data_hash[str(row_r[1])].name_long} {player_data_hash[str(row_r[1])].tags}")

    end_time_tags = time.perf_counter()
    print(f"Tempo de carregamento de tags.csv: {end_time_tags - start_time_tags:.2f} segundos")

    total_time = time.perf_counter() - start_time_total
    print(f"Tempo de carregamento total: {total_time:.2f} segundos")
    
    return player_data_hash


def player_query(query, player_data_hash):
    players = []
    player_ids_added = set()  # Cria um conjunto vazio para armazenar os ids dos jogadores adicionados

    for id, player_data in player_data_hash.items():
        for word in player_data.name_long.split():
            if query in word and id not in player_ids_added:
                players.append(player_data)
                player_ids_added.add(id)  # Adiciona o id do jogador ao conjunto para evitar duplicações


    players.sort(key=lambda player: player.rating, reverse=True)
    
    if players:
        print(f"{'sofifa_id':<10} {'short_name':<20} {'long_name':<45} {'player_positions':<20} {'rating':<10} {'count':<6}")
        for player in players:
            print(
                f"{player.id:<10} {player.name_short:<20} {player.name_long:<45} {','.join(player.positions):<20} {player.rating:<10.6f} {player.rating_count:<6}"
            )
    else:
        print(f"Nenhum jogador foi encontrado.")
        
        
def player_query2(query, player_data_hash, prefix_tree):
    players = []
    player_ids_added = set()  # Cria um conjunto vazio para armazenar os ids dos jogadores adicionados

    # Consulta a árvore de pesquisa em strings para obter os IDs dos jogadores

    for id in prefix_tree.get_children_with_prefix(query):
        player_ids_added.add(id)  # Adiciona o id do jogador ao conjunto para evitar duplicações

    # Obtém as informações complementares dos jogadores

    for id in player_ids_added:
        player_data = player_data_hash[id]
        players.append(player_data)

    # Ordena os jogadores pela classificação

    players.sort(key=lambda player: player.rating, reverse=True)

    # Imprime os resultados

    if players:
        print(f"{'sofifa_id':<10} {'short_name':<20} {'long_name':<45} {'player_positions':<20} {'rating':<10} {'count':<6}")
        for player in players:
            print(
                f"{player.id:<10} {player.name_short:<20} {player.name_long:<45} {','.join(player.positions):<20} {player.rating:<10.6f} {player.rating_count:<6}"
            )
    else:
        print(f"Nenhum jogador foi encontrado.")



def user_query(username, player_data_hash):
    players = []
    player_ids_added = set()  # Cria um conjunto vazio para armazenar os ids dos jogadores adicionados

    for id, player_data in player_data_hash.items():
        if player_data.user_ratings.get(str(username)):
            rating = player_data.user_ratings[str(username)]
            players.append((rating, id))
            player_ids_added.add(id)  # Adiciona o id do jogador ao conjunto para evitar duplicações

    players.sort(key=lambda rating_id: (rating_id[0], player_data_hash[rating_id[1]].rating), reverse=True)

    if players:
        print(f"{'sofifa_id':<10} {'short_name':<20} {'long_name':<45} {'global_rating':<15} {'count':<8} {'rating':<10}")
        for rating, id in players[:20]:
            player_data = player_data_hash[str(id)]
            print(
                f"{id:<10} {player_data.name_short:<20} {player_data.name_long:<45} {player_data.rating:<15.6f} {player_data.rating_count:<8} {rating:<10.1f}"
            )
    else:
        print(f"O usuário não foi encontrado.")




def top_query(position, player_data_hash, n):
    players = []
    player_ids_added = set()  # Cria um conjunto vazio para armazenar os ids dos jogadores adicionados

    for id, player_data in player_data_hash.items():
        if player_data.positions and any(position.strip().strip("'").strip('"') == pos.strip().strip("'").strip('"') for pos in player_data.positions) and player_data.rating_count >= 1000:
            players.append((player_data.rating, id))
            player_ids_added.add(id)  # Adiciona o id do jogador ao conjunto para evitar duplicações

    players.sort(key=lambda rating_id: rating_id[0], reverse=True)

    if players:
        print(f"{'sofifa_id':<10} {'short_name':<20} {'long_name':<45} {'player_positions':<20} {'nationality':<20} {'club_name':<10} {'league_name':<15} {'rating':<12} {'count':<6}")
        for rating, id in players[:n]:
            player_data = player_data_hash[id]
            print(
                f"{id:<10} {player_data.name_short:<20} {player_data.name_long:<45} {','.join(player_data.positions):<20} {player_data.nationality:<20} {player_data.club:<10} {player_data.league:<15} {player_data.rating:<12.6f} {player_data.rating_count:<6}"
            )
    else:
        print(f"Não há jogadores na posição {position} com pelo menos 1000 avaliações.")
        
        
        
def tag_query(tags, player_data_hash):
    players = []
    player_ids_added = set()  # Cria um conjunto vazio para armazenar os ids dos jogadores adicionados

    for id, player_data in player_data_hash.items():
        all_tags_match = True
        for tag in tags:
            tag = tag.strip().strip("'").strip('"')  # Limpa a tag
            if tag not in [player_tag.strip().strip("'").strip('"') for player_tag in player_data.tags]:
                all_tags_match = False
                break
        if all_tags_match:
            players.append((player_data.rating, id))
            player_ids_added.add(id)  # Adiciona o id do jogador ao conjunto para evitar duplicações

    players.sort(key=lambda rating_id: rating_id[0], reverse=True)

    if players:
        print(f"{'sofifa_id':<10} {'short_name':<20} {'long_name':<45} {'player_positions':<20} {'tags':<20} {'rating':<12} {'count':<6}")
        for rating, id in players:
            player_data = player_data_hash[id]
            print(
                f"{id:<10} {player_data.name_short:<20} {player_data.name_long:<45} {','.join(player_data.positions):<20} {','.join(player_data.tags):<20} {player_data.rating:<12.6f} {player_data.rating_count:<6}"
            )
    else:
        print(f"Não há jogadores associados às tags {tags}.")




def main():
    players_csv = "players.csv"
    ratings_csv = "rating.csv"
    tags_csv = "tags.csv"

    # Build the prefix tree
    prefix_tree = build_prefix_tree(players_csv)

    # Build the player data hash
    player_data_hash = build_player_data_hash(players_csv, ratings_csv, tags_csv)

    # Process the queries
    while True:
        query = input("Entre com uma consulta: ")

        if query == "exit":
            break

        if query.startswith("player "):
            player_query(query[7:], player_data_hash)
        elif query.startswith("user "):
            user_query(int(query[5:]), player_data_hash)
        elif query.startswith("top "):
            try:
                print(f"{query.split(' ')}")
                starts, n, position = query.split(" ", maxsplit=3)
                n = int(n.strip())
                top_query(position, player_data_hash, n)
            except (ValueError, IndexError):
                print(f"Formato de consulta inválido: {query}")
        elif query.startswith("tags "):
            try:
                tags = query[5:].split(" ")
                print(f"{tags[0]}")
                tag_query(tags, player_data_hash)
            except (ValueError, IndexError):
                print(f"Formato de consulta inválido: {query}")
        else:
            print("Consulta inválida")


if __name__ == "__main__":
    main()
