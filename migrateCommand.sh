
flask db init
flask db migrate -m "ajout lange reglemntation et supprimer de l'artle"
flask db upgrade


flask db init
flask db migrate -m "ajout attribution auto des reglemnatations"
flask db upgrade
