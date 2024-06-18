# robot_auction_api

This repository has code for a public robot services exchange.

The purpose is to facilitate robot services buying and selling.

This will speed the adoption of robot services, which is good.

The system is an exchange, but instead of selling stocks or ad impressions, we're selling robot services.

Like a job board for robots.

![Description](images/weird.png)

There are three parts:
* buyer client (https://github.com/MevlutArslan/robot-auction-frontend)
* seller client 
* exchange

The buyer client interacts with the exchange API through the /make_bid route.
The seller client interacts with the exchange API through the /grab_job route.

A buyer may set a bid for a certain (service, location, time, price) tuple.
A seller submits a request for a job with a (service, location, time) tuple, and receives the highest price matching bid.

The deal is struck and the buyer pays, the robot performs the service, and then the seller is paid.

