curl http://localhost:5000/ping

BIDURL="http://localhost:5000/make_bid"
curl --header "Content-Type: application/json" --data '{"username":"xyz","password":"xyz"}' $BIDURL 
