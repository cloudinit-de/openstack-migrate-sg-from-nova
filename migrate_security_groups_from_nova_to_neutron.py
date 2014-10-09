#!/usr/bin/env python

import MySQLdb
import uuid

nova_db = MySQLdb.connect("localhost","root","","nova")
neutron_db = MySQLdb.connect("localhost","root","","neutron")

nova_conn = nova_db.cursor()
neutron_conn = neutron_db.cursor()

#neutron_conn.execute('delete from securitygroupportbindings')
#neutron_conn.execute('delete from securitygrouprules')
#neutron_conn.execute('delete from securitygroups')
#neutron_db.commit()

nova_conn.execute('select id, project_id, name, description from security_groups where deleted_at IS NULL and deleted=0')
nova_sg = nova_conn.fetchall()

for sg in nova_sg:
    sg_id = sg[0]
    neutron_sg_id = str(uuid.uuid4())
    neutron_sg_name = sg[2]
    neutron_sg_desc = sg[3]
    neutron_sg_tenant_id = sg[1]
    set_sg = "insert into securitygroups (tenant_id, id, name, description) VALUES ('%s', '%s', '%s', '%s')" % (neutron_sg_tenant_id, neutron_sg_id, neutron_sg_name, neutron_sg_desc)
    neutron_conn.execute(set_sg)
    get_sg_rules = "select id, protocol, from_port, to_port, cidr from security_group_rules where parent_group_id = %d and deleted_at IS NULL and deleted=0" % sg_id
    nova_conn.execute(get_sg_rules)
    nova_sg_rules = nova_conn.fetchall()

    for nova_sg_rule in nova_sg_rules:
        nova_sg_rule_id = nova_sg_rule[0]
        neutron_sg_rule_id = str(uuid.uuid4())
        nova_sg_rule_protocol = nova_sg_rule[1]
        nova_sg_rule_min_port = nova_sg_rule[2]
        nova_sg_rule_max_port = nova_sg_rule[3]
        nova_sg_rule_remote_ip_prefix = nova_sg_rule[4]
        if nova_sg_rule_protocol == 'icmp':
            set_sg_rules = """insert into securitygrouprules (tenant_id, id, security_group_id, direction, ethertype, protocol, port_range_min, port_range_max, remote_ip_prefix)
                           VALUES ('%s', '%s', '%s', 'ingress', 'IPv4', '%s', NULL, NULL, '%s')""" % (neutron_sg_tenant_id, neutron_sg_rule_id, neutron_sg_id, nova_sg_rule_protocol, 
                                                                                                  nova_sg_rule_remote_ip_prefix)
        else:
            set_sg_rules = """insert into securitygrouprules (tenant_id, id, security_group_id, direction, ethertype, protocol, port_range_min, port_range_max, remote_ip_prefix)
                           VALUES ('%s', '%s', '%s', 'ingress', 'IPv4', '%s', %d, %d, '%s')""" % (neutron_sg_tenant_id, neutron_sg_rule_id, neutron_sg_id, nova_sg_rule_protocol,   
                                                                                             nova_sg_rule_min_port, nova_sg_rule_max_port, nova_sg_rule_remote_ip_prefix)
        neutron_conn.execute(set_sg_rules)


    get_sg_instance_assoc = "select instance_uuid from security_group_instance_association where security_group_id = %s AND deleted_at IS NULL and deleted=0" % sg_id
    nova_conn.execute(get_sg_instance_assoc)
    nova_sg_instance_assoc = nova_conn.fetchall()

    for nova_sg_instance_assoc_item in nova_sg_instance_assoc:
        nova_sg_instance_uuid = nova_sg_instance_assoc_item[0]
        get_sg_instance_port_assoc = "select id from ports where device_owner = 'compute:None' AND device_id = '%s'" % nova_sg_instance_uuid
        neutron_conn.execute(get_sg_instance_port_assoc)
        sg_instance_port_assoc = neutron_conn.fetchall()

        for i in sg_instance_port_assoc:
            #print i[0] + "   " + neutron_sg_id
            set_sg_instance_port_assoc = "insert into securitygroupportbindings (port_id, security_group_id) VALUES ('%s', '%s')" % (i[0], neutron_sg_id)
            neutron_conn.execute(set_sg_instance_port_assoc)

neutron_db.commit()
