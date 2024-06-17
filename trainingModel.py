import tensorflow as tf
import cv2
import numpy as np  # Importér numpy
import os
import yaml
from sklearn.model_selection import train_test_split
from tensorflow.keras.utils import Sequence

class CustomDataGenerator(Sequence):
    def __init__(self, image_dir, label_dir, class_names, batch_size=32, image_size=(224, 224), shuffle=True):
        self.image_dir = image_dir
        self.label_dir = label_dir
        self.class_names = class_names
        self.batch_size = batch_size
        self.image_size = image_size
        self.shuffle = shuffle
        self.image_files = [f for f in os.listdir(image_dir) if f.endswith('.jpg')]
        self.on_epoch_end()

    def __len__(self):
        return int(np.floor(len(self.image_files) / self.batch_size))

    def __getitem__(self, index):
        batch_files = self.image_files[index * self.batch_size:(index + 1) * self.batch_size]
        images, labels = self.__data_generation(batch_files)
        return images, labels

    def on_epoch_end(self):
        if self.shuffle:
            np.random.shuffle(self.image_files)

    def __data_generation(self, batch_files):
        images = []
        labels = []
        for file in batch_files:
            img_path = os.path.join(self.image_dir, file)
            image = cv2.imread(img_path)
            image = cv2.resize(image, self.image_size)
            image = image / 255.0
            images.append(image)
            
            label_path = os.path.join(self.label_dir, os.path.splitext(file)[0] + '.txt')
            label = self.__read_label(label_path)
            labels.append(label)
            
        return np.array(images), np.array(labels)

    def __read_label(self, label_path):
        with open(label_path, 'r') as file:
            lines = file.readlines()
        labels = np.zeros(len(self.class_names))
        for line in lines:
            class_id = int(line.split()[0])
            labels[class_id] = 1  # Assuming binary labels for simplicity
        return labels

# Læs data.yaml filen for at få klassenavne og antal klasser
with open('training/data.yaml', 'r') as file:
    data_config = yaml.safe_load(file)
    
class_names = data_config['names']
num_classes = data_config['nc']

# Datastier
image_dir = 'training/train/images'
label_dir = 'training/train/labels'

# Opret og opdel data i træning og validering
image_files = [f for f in os.listdir(image_dir) if f.endswith('.jpg')]
train_files, val_files = train_test_split(image_files, test_size=0.2)

# Opret CustomDataGenerator instanser
train_generator = CustomDataGenerator(image_dir, label_dir, class_names, batch_size=32, shuffle=True)
val_generator = CustomDataGenerator(image_dir, label_dir, class_names, batch_size=32, shuffle=False)

# Byg og træn modellen
model = tf.keras.models.Sequential([
    tf.keras.layers.Input(shape=(224, 224, 3)),
    tf.keras.layers.Conv2D(32, (3, 3), activation='relu'),
    tf.keras.layers.MaxPooling2D((2, 2)),
    tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
    tf.keras.layers.MaxPooling2D((2, 2)),
    tf.keras.layers.Conv2D(128, (3, 3), activation='relu'),
    tf.keras.layers.MaxPooling2D((2, 2)),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(512, activation='relu'),
    tf.keras.layers.Dense(num_classes, activation='softmax')  # Brug softmax for multiple classes
])

model.compile(optimizer='adam',
              loss='categorical_crossentropy',  # Brug categorical_crossentropy for multiple classes
              metrics=['accuracy'])

model.fit(train_generator, validation_data=val_generator, epochs=10)

# Gem modellen
model.save('model.h5')
