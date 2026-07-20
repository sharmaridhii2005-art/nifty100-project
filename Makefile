load:
	python src/etl/loader.py

test:
	pytest tests/

report:
	python src/etl/validator.py

clean:
	rm -rf output/*.csv
	rm -rf logs/*

ratios:
	python src/etl/ratios.py

dashboard:
	echo "Dashboard module will run here"

api:
	echo "API module will run here"