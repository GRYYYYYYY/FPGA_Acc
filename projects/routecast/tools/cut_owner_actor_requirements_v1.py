"""Necessary changed NETs for realizing one fixed unit-owner allocation."""
def required_actors(allocation,ownership,complete_CID_domains):
 missing=sorted({net for node,net in allocation.items() if node not in ownership.get(net,set())})
 displaced=sorted({owner for node,net in allocation.items() for owner,nodes in ownership.items() if owner!=net and node in nodes})
 actors=sorted(set(missing)|set(displaced));covered=set(complete_CID_domains)
 return dict(missing_assigned_points_NETs=missing,displaced_current_owner_NETs=displaced,required_actor_NETs=actors,new_actor_NETs=sorted(set(actors)-set(ownership)),existing_actor_NETs=sorted(set(actors)&set(ownership)),actors_missing_all_CID_domain_proofs=sorted(set(actors)-covered))
