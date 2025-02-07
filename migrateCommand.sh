
flask db init
flask db migrate -m "ajout lange reglemntation et supprimer de l'artle"
flask db upgrade


flask db init
flask db migrate -m "ajout attribution auto des reglemnatations"
flask db upgrade

flask db init
flask db migrate -m "applicable et conforme boolein "
flask db upgrade


flask db migrate -m "add score "
flask db upgrade

flask db migrate -m "tester uuid"


flask db migrate -m "ajout suppression automatique des relation entreprises"

flask db migrate -m "ajout csacsad all"

flask db migrate -m "nouvelle modele"