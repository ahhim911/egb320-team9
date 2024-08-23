import pygame
import time

# Define colors
BLACK = (100, 100, 100)
WHITE = (180, 180, 180)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
SHELF_BLUE = (100, 100, 255)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
YELLOW = (255, 255, 0)

class Node:
    def __init__(self, x, y, is_obstacle):
        self.x = x
        self.y = y
        self.is_obstacle = is_obstacle
        self.g_cost = float('inf')
        self.h_cost = 0
        self.f_cost = float('inf')
        self.parent = None

def heuristic(a, b):
    (x1, y1) = a
    (x2, y2) = b
    return abs(x1 - x2) + abs(y1 - y2)

def a_star_search(maze, start, end):
    open_list = [maze[start[0]][start[1]]]
    closed_list = []

    maze[start[0]][start[1]].g_cost = 0
    maze[start[0]][start[1]].f_cost = heuristic(start, end)

    while open_list:
        current_node = min(open_list, key=lambda x: x.f_cost)
        if current_node == maze[end[0]][end[1]]:
            path = []
            while current_node.parent:
                path.append((current_node.x, current_node.y))
                current_node = current_node.parent
            path.append((start[0], start[1]))
            path.reverse()
            return path

        open_list.remove(current_node)
        closed_list.append(current_node)

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            neighbor_x, neighbor_y = current_node.x + dx, current_node.y + dy
            if 0 <= neighbor_x < len(maze) and 0 <= neighbor_y < len(maze[0]) and not maze[neighbor_x][neighbor_y].is_obstacle:
                neighbor = maze[neighbor_x][neighbor_y]
                temp_g_cost = current_node.g_cost + 1
                if temp_g_cost < neighbor.g_cost:
                    neighbor.parent = current_node
                    neighbor.g_cost = temp_g_cost
                    neighbor.f_cost = neighbor.g_cost + heuristic((neighbor.x, neighbor.y), end)
                    if neighbor not in open_list:
                        open_list.append(neighbor)

    return None

def draw_maze(screen, maze, path=None):
    screen.fill(WHITE)
    cell_size = 20

    for i in range(len(maze)):
        for j in range(len(maze[0])):
            if maze[i][j].is_obstacle:
                pygame.draw.rect(screen, BLACK, (j * cell_size, i * cell_size, cell_size, cell_size))
                if maze_matrix[i][j] == 'p':
                    pygame.draw.rect(screen, YELLOW, (j * cell_size, i * cell_size, cell_size, cell_size))
                if maze_matrix[i][j] == 'b':
                    pygame.draw.rect(screen, SHELF_BLUE, (j * cell_size, i * cell_size, cell_size, cell_size))
            else:
                pygame.draw.rect(screen, (240, 240, 240), (j * cell_size, i * cell_size, cell_size, cell_size), 1)
                if maze[i][j].f_cost != float('inf'):
                    font = pygame.font.Font(None, 16)
                    text = font.render(str(int(maze[i][j].g_cost)), True, GRAY)
                    text_rect = text.get_rect(center=(j * cell_size + cell_size // 2, i * cell_size + cell_size // 2))
                    screen.blit(text, text_rect)

    if path:
        for x, y in path:
            pygame.draw.rect(screen, GREEN, (y * cell_size, x * cell_size, cell_size, cell_size))

    pygame.draw.rect(screen, RED, (start[1] * cell_size, start[0] * cell_size, cell_size, cell_size))
    pygame.draw.rect(screen, BLUE, (end[1] * cell_size, end[0] * cell_size, cell_size, cell_size))
    pygame.display.flip()

if __name__ == "__main__":
    # Define the maze
    global maze_matrix

    maze_matrix = [
        ['p', 'p', 'e', 0  , 0  , 0  , 'b', 'b'    , 'b', 'b', 'b'    , 'b', 'b', 'b'    , 'b', 'b', 'b'    , 'b'],
        ['p', 'p', 'p', 0  , 0  , 0  , 0  , '0-1'  , 0  , 0  , '0-2'  , 0  , 0  , '0-3'  , 0  , 0  , '0-4'  , 0  ],
        ['p', 'p', 'p', 0  , 0  , 0  , 0  , 0      , 0  , 0  , 0      , 0  , 0  , 0      , 0  , 0  , 0      , 0  ],
        [0  , 0  , 0  , 0  , 0  , 0  , 0  , 0      , 0  , 0  , 0      , 0  , 0  , 0      , 0  , 0  , 0      , 0  ],
        [0  , 0  , 0  , 0  , 0  , 0  , 0  , '1-1'  , 0  , 0  , '1-2'  , 0  , 0  , '1-3'  , 0  , 0  , '1-4'  , 0  ],
        [0  , 0  , 0  , 0  , 0  , 0  , 'b', 'b'    , 'b', 'b', 'b'    , 'b', 'b', 'b'    , 'b', 'b', 'b'    , 'b'],
        [0  , 0  , 0  , 0  , 0  , 0  , 'b', 'b'    , 'b', 'b', 'b'    , 'b', 'b', 'b'    , 'b', 'b', 'b'    , 'b'],
        [0  , 0  , 0  , 0  , 0  , 0  , 0  , '2-1'  , 0  , 0  , '2-2'  , 0  , 0  , '2-3'  , 0  , 0  , '2-4'  , 0  ],
        [0  , 0  , 0  , 0  , 0  , 0  , 0  , 0      , 0  , 0  , 0      , 0  , 0  , 0      , 0  , 0  , 0      , 0  ],
        [0  , 0  , 0  , 0  , 0  , 0  , 0  , 0      , 0  , 0  , 0      , 0  , 0  , 0      , 0  , 0  , 0      , 0  ],
        [0  , 0  , 0  , 0  , 0  , 0  , 0  , '3-1'  , 0  , 0  , '3-2'  , 0  , 0  , '3-3'  , 0  , 0  , '3-4'  , 0  ],
        [0  , 0  , 0  , 0  , 0  , 0  , 'b', 'b'    , 'b', 'b', 'b'    , 'b', 'b', 'b'    , 'b', 'b', 'b'    , 'b'],
        [0  , 0  , 0  , 0  , 0  , 0  , 'b', 'b'    , 'b', 'b', 'b'    , 'b', 'b', 'b'    , 'b', 'b', 'b'    , 'b'],
        [0  , 0  , 0  , 0  , 0  , 0  , 0  , '4-1'  , 0  , 0  , '4-2'  , 0  , 0  , '4-3'  , 0  , 0  , '4-4'  , 0  ],
        [0  , 0  , 0  , 0  , 0  , 0  , 0  , 0      , 0  , 0  , 0      , 0  , 0  , 0      , 0  , 0  , 0      , 0  ],
        [0  , 0  , 0  , 0  , 0  , 0  , 0  , 0      , 0  , 0  , 0      , 0  , 0  , 0      , 0  , 0  , 0      , 0  ],
        [0  , 's', 0  , 0  , 0  , 0  , 0  , '5-1'  , 0  , 0  , '5-2'  , 0  , 0  , '5-3'  , 0  , 0  , '5-4'  , 0  ],
        [0  , 0  , 0  , 0  , 0  , 0  , 'b', 'b'    , 'b', 'b', 'b'    , 'b', 'b', 'b'    , 'b', 'b', 'b'    , 'b'],
    ]

    # Create the maze from the matrix
    maze = [[Node(i, j, (maze_matrix[i][j] == 1 or maze_matrix[i][j] == 'p' or maze_matrix[i][j] == 'b')) for j in range(len(maze_matrix[0]))] for i in range(len(maze_matrix))]

    start_point = 's'
    end_point = '0-4'

    start = None
    end = None
    for i in range(len(maze_matrix)):
        for j in range(len(maze_matrix[0])):
            if maze_matrix[i][j] == start_point: 
                print("start pt: ", i, j)
                start = (i, j)
            elif maze_matrix[i][j] == end_point:
                print("end pt: ", i, j)
                end = (i, j)

    if start is None or end is None:
        print("Invalid maze: Start or end point not found.")
        exit()
    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((360, 360)) # (width, height)
    pygame.display.set_caption("A* Pathfinding Visualization")

    # Run the A* search and visualize the path
    path = a_star_search(maze, start, end)
    if path:
        for i in range(len(path)):
            draw_maze(screen, maze, path[:i+1])
            time.sleep(0.1)
    else:
        print("No path found.")

    # Wait for the user to close the window
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
    pygame.quit()