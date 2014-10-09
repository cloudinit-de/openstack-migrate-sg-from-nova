openstack-migrate-sg-from-nova
==============================

Migration script for nova security group tables to neutron security group tables

This script transfers entries from the nova security group tables into neutron tables. Be careful to comment in the first delete from lines!

What it does:
* keeps group names and tenant assiciations
* keeps inbound rules for groups
* keeps group/port assiciations

Feel free to beautify and/or improve (i know it looks ugly) - it simply works. 
