import numpy as np

# Загружаем матрицы из файлов
data_matrix = np.loadtxt("player_stats_matrix.txt", delimiter=",")
ratings_matrix = np.loadtxt("player_ratings_matrix.txt", delimiter=",")
weights = np.loadtxt("player_weights_matrix.txt", delimiter=",")

# Функция для расчета рейтинга по весам
def calculate_rating(player_stats, weights):
    return np.dot(player_stats, weights[:-1]) + weights[-1]

# Вычисляем рейтинг для каждого игрока и сравниваем с реальным
predicted_ratings = []
errors = []

print("-" * 50)
print("|{:^15}|{:^15}|{:^15}|".format("Реальный рейтинг", "Предсказанный рейтинг", "Погрешность"))
print("-" * 50)

for i in range(len(data_matrix)):
    player_stats = data_matrix[i]
    real_rating = ratings_matrix[i]
    predicted_rating = calculate_rating(player_stats, weights)
    error = abs(real_rating - predicted_rating)

    predicted_ratings.append(predicted_rating)
    errors.append(error)
    print("|{:^15.2f}|{:^15.2f}|{:^15.2f}|".format(real_rating, predicted_rating, error))

print("-" * 50)

# Вычисляем общую погрешность в %
average_error = np.mean(errors)
average_rating = np.mean(ratings_matrix)
total_error_percent = (average_error / average_rating) * 100

print(f"Общая погрешность: {total_error_percent:.2f}%")

# Функция для конвертации статистики
def convert_stats(kdr, total_kills, total_deaths, damage_per_round, rounds, headshot_percent):
    kills_per_round = total_kills / rounds
    assists_per_round = (total_kills / kdr - total_deaths) / rounds
    headshot_percent = headshot_percent / 100  # Конвертируем из формата 45, 50, 53 в 0.45, 0.50, 0.53
    return np.array([kdr, damage_per_round, kills_per_round, assists_per_round, headshot_percent])

# Предлагаем пользователю ввести свою статистику
while True:
    try:
        kdr = float(input("Введите ваш K/D Ratio: "))
        total_kills = int(input("Введите ваше общее количество убийств: "))
        total_deaths = int(input("Введите ваше общее количество смертей: "))
        damage_per_round = float(input("Введите ваш Damage / Round: "))
        rounds = int(input("Введите общее количество раундов: "))
        headshot_percent = float(input("Введите ваш Headshot % (например, 45, 50, 53): "))

        user_stats_converted = convert_stats(kdr, total_kills, total_deaths, damage_per_round, rounds, headshot_percent)
        user_predicted_rating = calculate_rating(user_stats_converted, weights)

        print(f"Ваш предсказанный рейтинг: {user_predicted_rating:.2f}")
        break

    except ValueError:
        print("Некорректный ввод. Пожалуйста, введите числовые значения.")
