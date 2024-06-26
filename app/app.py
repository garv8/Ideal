from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
)
import markdown
from llm.nutrition_functions import main
from llm.openai_utils import (
    complete_workout,
)
from llm.calculations import calculate_daily_recommendations, count_nutrients
from llm.recipe_utils import (
    display_recipes_grid,
    get_recipe_details,
    get_recipe_nutrients,
)
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SESSIONS_SECRET")

saveApi = False


# Frontend routes
@app.route("/")
def home():
    return render_template("home/index.html")


@app.route("/builder", methods=["GET", "POST"])
def builder():

    if request.method == "POST":
        session["current_weight"] = request.form.get("current_weight")
        session["ideal_weight"] = request.form.get("ideal_weight")
        session["body_goal"] = request.form.get("body_goal")
        session["age"] = request.form.get("age")
        session["height"] = request.form.get("height")
        session["sex"] = request.form.get("sex")
        session["allergies"] = request.form.get("allergies")
        session["diet"] = request.form.get("diet")
        session["religion"] = request.form.get("religion")
        session["anything_else_diet"] = request.form.get("anything_else")
        session["physical_impediments"] = request.form.get("physical_impediments")
        calculate_daily_recommendations(session)
        return redirect("/dashboard")
    return render_template("builder/index.html")


@app.route("/dashboard", methods=["GET"])
def dashboard():
    return render_template("dashboard/index.html")


@app.route("/get_nutrients", methods=["GET"])
def get_nutrients():
    return render_template("dashboard/nutrients_left.html")


# Backend routes
@app.route("/generate_workout_calisthenics", methods=["GET"])
def generate_workout_calisthenics():

    # For when save money
    if saveApi:
        return {}

    # Work with tabs
    # if session.get("workout_calisthenics"):
    #     return render_template(
    #         "dashboard/workout.html", workout=session["workout_calisthenics"]
    #     )

    session["workout_calisthenics"] = complete_workout(session, "Calisthenics")
    return render_template(
        "dashboard/workout.html", workout=session["workout_calisthenics"]
    )


@app.route("/generate_workout_weights", methods=["GET"])
def generate_workout_weights():

    # For when save money
    if saveApi:
        return {}

    session["workout_weights"] = complete_workout(session, "weight lifiting")
    return render_template("dashboard/workout.html", workout=session["workout_weights"])


@app.route("/generate_workout_cardio", methods=["GET"])
def generate_workout_cardio():

    # For when save money
    if saveApi:
        return {}

    session["workout_cardio"] = complete_workout(session, "Cardio")
    return render_template("dashboard/workout.html", workout=session["workout_cardio"])


@app.route("/generate-recipes", methods=["GET"])
def generate_recipes():

    # for when no api
    if saveApi:
        return {}

    recipes_list = display_recipes_grid(session)
    return render_template("dashboard/recipes.html", data=recipes_list)


@app.route("/generate", methods=["GET", "POST"])
def generate():
    if request.method == "POST":

        user_input = request.form["user_input"]
        response, recipeId = main(
            session["allergies"], session["diet"], session["religion"], user_input
        )  # Wrap the response in a Bootstrap card component

        md_template_string = markdown.markdown(response, output_format="html")
        # return md_template_string
        return f"""

            <div class="container mt-3 justify-content-center"> 
                <div id='chat-response' class='mb-3 justify-content-center'>{md_template_string}</div>
                <div class="row mb-3">
                    <div class="col-6 d-flex justify-content-end pr-2"> 
                        <button type="button" class="btn btn-success" hx-target="#nutrients_left" hx-post="/update_nutrients?recipe_id={recipeId}" hx-trigger="click">Eat me!</button>
                    </div>
                    <div class="col-6 d-flex justify-content-start pl-2">
                         <button type="button" class="btn btn-success" data-bs-toggle="modal" data-bs-target="#recipeModal" hx-get="/recipes?recipe_id={recipeId}" hx-target="#recipe-modal-body" hx-trigger="click">Show Recipe Details</button>
                    </div>
                </div>
            </div>

            """

    return render_template("index.html")


@app.route("/recipes", methods=["GET"])
def recipes():
    if request.method == "GET":
        recipe_id = request.args.get("recipe_id")
        if recipe_id:
            session["recipe_data"] = get_recipe_details(recipe_id)
            return render_template("dashboard/recipe_details.html")
    return "Error", 404


@app.route("/update_nutrients", methods=["POST"])
def update_nutrients():
    recipe_id = request.args.get("recipe_id")
    recipe = get_recipe_nutrients(recipe_id)
    if recipe:
        count_nutrients(recipe, session)
        return render_template("dashboard/nutrients_left.html")
    return "Error", 404


@app.route("/userInputNutrients", methods=["POST"])
def userInputNutrients():
    print("values are ", request.form.get("calories"))
    session["daily_calories"] = int(request.form.get("calories"))
    session["daily_protein_grams"] = int(request.form.get("protein"))
    session["daily_carbs_grams"] = int(request.form.get("carbohydrates"))
    session["daily_fats_grams"] = int(request.form.get("fats"))
    print("Here")
    return render_template("dashboard/nutrients_left.html")
    return "", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
