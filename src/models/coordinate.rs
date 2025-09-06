use serde::{Serialize, Deserialize};

use crate::models::region::RegionCoordinate;

#[derive(Debug, Serialize, Deserialize)]
pub struct Coordinate {
    pub query_id: String,
    pub query_name: String,
    pub query_type: String,
    pub rcv: Vec<RegionCoordinate>,
    #[serde(default = "default_strand")]
    pub strand: String,
}

fn default_strand() -> String {
    "pos".to_string()
}
