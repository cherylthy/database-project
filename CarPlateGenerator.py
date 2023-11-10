import random
import csv

def generate_license_plate():
    vehicle_class = 'S'
    alphabet_series = random.choice('JKLMN')
    if alphabet_series == 'N':
        last_letters = 'ABCDEFGHJKLMN'
    else:
        last_letters = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
    last_letter = random.choice(last_letters)
    numerical_series = str(random.randint(1000, 9999))
    checksum_letters = 'ABCDEGHJKLMNPQRTUXYZ'
    checksum_letter = random.choice(checksum_letters)
    license_plate_number = f"{vehicle_class}{alphabet_series}{last_letter}{numerical_series}{checksum_letter}"
    return license_plate_number

# Generating license plates
num_plates = 492
data = [generate_license_plate() for _ in range(num_plates)]

# Writing to CSV
with open('license_plates.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['License Plates'])
    writer.writerows([[plate] for plate in data])

print(f"{num_plates} license plates have been generated and written to 'license_plates.csv'.")
