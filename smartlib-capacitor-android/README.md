# SmartLib Capacitor Android

This project integrates the SmartLib application with Capacitor for Android. Below are the details and instructions for setting up and running the project.

## Project Structure

The project is organized as follows:

```
smartlib-capacitor-android
├── android                # Android-specific files
│   ├── app
│   │   ├── src
│   │   │   ├── main
│   │   │   │   ├── assets # Static assets (HTML, CSS, JS)
│   │   │   │   ├── java   # Java source code
│   │   │   │   └── res    # Resources (drawables, layouts, etc.)
│   │   └── build.gradle    # Gradle build configuration for the app
│   ├── gradle              # Gradle wrapper files
│   ├── gradle.properties    # Gradle configuration properties
│   ├── settings.gradle      # Modules included in the project
│   └── build.gradle         # Top-level Gradle build configuration
├── src
│   └── web                 # Web assets and code for Capacitor
├── capacitor.config.ts      # Capacitor project configuration
├── package.json             # npm configuration file
├── tsconfig.json            # TypeScript configuration file
└── README.md                # Project documentation
```

## Getting Started

### Prerequisites

- Node.js (version 12 or later)
- npm (Node Package Manager)
- Android Studio
- Java Development Kit (JDK)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd smartlib-capacitor-android
   ```

2. Install the dependencies:
   ```
   npm install
   ```

3. Open the Android project in Android Studio:
   - Navigate to the `android` directory and open it as a project.

### Running the App

1. Connect an Android device or start an Android emulator.
2. Run the following command to build and deploy the app:
   ```
   npx cap run android
   ```

### Development

- Place your web assets (HTML, CSS, JS) in the `src/web` directory.
- Modify the Java code in `android/app/src/main/java` as needed for your application logic.
- Update resources in the `android/app/src/main/res` directory for UI elements.

### Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

### License

This project is licensed under the MIT License. See the LICENSE file for more details.