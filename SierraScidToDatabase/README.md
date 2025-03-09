Just setting up some simple code for connecting sierra charts to a local python script to flush data to a postgres database. Still need to write the ACSIL code to send the data to python server.


- Why do this? 
- - Well I'm cheap and don't want to pay for another data API when I already pay for Sierra charts data. 
- Why not use DTC? 
- - DTC doesn't let you stream CME group data so we have to be creative. I could setup something to parse scid files but I don't need tick-by-tick data so I decided to set up a simple TCP network to send data.   

`sierra_nw_connection.py` is the server side of things, it makes use of multi threading to handle multiple connections from clients (aka different symbols from sierra charts). We make use of TCP because it's easy to work with and does its job very well.

`server_testing.py` is just a quick script to check if the server code is correctly handling connections and putting data into the database. 

The other files are utility functions that may or may not be helpful down the road