
import os

from flask import (
    Flask, render_template, request,
    redirect, url_for, flash
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from sqlalchemy.engine import make_url


app = Flask(__name__)

# Configuration
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "cle-locale-a-remplacer"
)

# Base de données :
# PostgreSQL en production, SQLite en local.
database_url = os.environ.get("DATABASE_URL")

if database_url:
    # Certains fournisseurs donnent encore postgres://
    # SQLAlchemy attend postgresql://
    parsed_url = make_url(database_url)

    if parsed_url.drivername == "postgres":
        parsed_url = parsed_url.set(
            drivername="postgresql"
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        parsed_url.render_as_string(hide_password=False)
    )
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///contacts.db"
    )

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# Modèle de données
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    entreprise = db.Column(db.String(150), default="")

    def __repr__(self):
        return f"<Contact {self.prenom} {self.nom}>"


# Création de la table si elle n'existe pas
with app.app_context():
    db.create_all()


# READ : afficher les contacts et rechercher
@app.route("/")
def index():
    recherche = request.args.get("q", "").strip()

    requete = Contact.query

    if recherche:
        terme = f"%{recherche}%"
        requete = requete.filter(
            or_(
                Contact.nom.ilike(terme),
                Contact.prenom.ilike(terme),
                Contact.email.ilike(terme),
                Contact.telephone.ilike(terme),
                Contact.entreprise.ilike(terme),
            )
        )

    contacts = requete.order_by(
        Contact.nom.asc(),
        Contact.prenom.asc()
    ).all()

    total = Contact.query.count()

    return render_template(
        "index.html",
        contacts=contacts,
        recherche=recherche,
        total=total
    )


# CREATE : ajouter un contact
@app.route("/ajouter", methods=["POST"])
def ajouter():
    nom = request.form.get("nom", "").strip()
    prenom = request.form.get("prenom", "").strip()
    telephone = request.form.get("telephone", "").strip()
    email = request.form.get("email", "").strip()
    entreprise = request.form.get("entreprise", "").strip()

    if not all([nom, prenom, telephone, email]):
        flash("Veuillez remplir tous les champs obligatoires.", "error")
        return redirect(url_for("index"))

    if "@" not in email or "." not in email.split("@")[-1]:
        flash("Veuillez saisir une adresse e-mail valide.", "error")
        return redirect(url_for("index"))

    contact = Contact(
        nom=nom,
        prenom=prenom,
        telephone=telephone,
        email=email,
        entreprise=entreprise
    )

    db.session.add(contact)
    db.session.commit()

    flash("Contact ajouté avec succès.", "success")
    return redirect(url_for("index"))


# UPDATE : modifier un contact
@app.route("/modifier/<int:contact_id>", methods=["POST"])
def modifier(contact_id):
    contact = db.get_or_404(Contact, contact_id)

    nom = request.form.get("nom", "").strip()
    prenom = request.form.get("prenom", "").strip()
    telephone = request.form.get("telephone", "").strip()
    email = request.form.get("email", "").strip()
    entreprise = request.form.get("entreprise", "").strip()

    if not all([nom, prenom, telephone, email]):
        flash("Les champs obligatoires sont manquants.", "error")
        return redirect(url_for("index"))

    if "@" not in email or "." not in email.split("@")[-1]:
        flash("Veuillez saisir une adresse e-mail valide.", "error")
        return redirect(url_for("index"))

    contact.nom = nom
    contact.prenom = prenom
    contact.telephone = telephone
    contact.email = email
    contact.entreprise = entreprise

    db.session.commit()

    flash("Contact modifié avec succès.", "success")
    return redirect(url_for("index"))


# DELETE : supprimer un contact
@app.route("/supprimer/<int:contact_id>", methods=["POST"])
def supprimer(contact_id):
    contact = db.get_or_404(Contact, contact_id)

    db.session.delete(contact)
    db.session.commit()

    flash("Contact supprimé.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)