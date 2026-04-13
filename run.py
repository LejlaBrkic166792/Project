from flaskr import create_app

app = create_app()

if __name__ == "__main__":
    # Usa debug=True per vedere gli errori nel browser
    app.run(debug=True)