import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model

# 1. Setup Data Paths and Sizes
DATA_DIR = 'data'
IMG_SIZE = (224, 224) # MobileNetV2's favorite image size
BATCH_SIZE = 32

# 2. Load the Images from your Folders
print("Loading datasets...")
train_dataset = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2, # Uses 80% for training
    subset="training",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

val_dataset = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2, # Saves 20% to test the AI's accuracy
    subset="validation",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

class_names = train_dataset.class_names
print(f"Classes found: {class_names}")

# Optimize data loading for faster training
AUTOTUNE = tf.data.AUTOTUNE
train_dataset = train_dataset.prefetch(buffer_size=AUTOTUNE)
val_dataset = val_dataset.prefetch(buffer_size=AUTOTUNE)

# 3. Build the MobileNetV2 Model (Transfer Learning)
print("Downloading and building MobileNetV2...")

# This automatically formats the pixels the way MobileNetV2 expects
preprocess_input = tf.keras.applications.mobilenet_v2.preprocess_input

# Load the base model (pre-trained on millions of images)
base_model = MobileNetV2(input_shape=IMG_SIZE + (3,), include_top=False, weights='imagenet')
base_model.trainable = False # Freeze it so we don't destroy its existing knowledge

# Add our custom layers on top for the 3 Potato classes
inputs = tf.keras.Input(shape=IMG_SIZE + (3,))
x = preprocess_input(inputs)
x = base_model(x, training=False)
x = GlobalAveragePooling2D()(x)
x = Dropout(0.2)(x) # Helps prevent the model from memorizing the data
outputs = Dense(len(class_names), activation='softmax')(x)

model = Model(inputs, outputs)

# 4. Compile the Model
model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

# 5. Train the Model!
print("Starting training...")
EPOCHS = 5 # Running it 5 times through the data is enough for a strong prototype
history = model.fit(train_dataset, validation_data=val_dataset, epochs=EPOCHS)

# 6. Save the finished brain
model.save('potato_disease_model.keras')
print("Model saved successfully as 'potato_disease_model.keras'!")