#![allow(clippy::all)]

use multiversx_sc::derive_imports::*;
use multiversx_sc::imports::*;

#[type_abi]
#[derive(TopEncode, TopDecode, NestedEncode, NestedDecode, Clone)]
pub struct Post<M: ManagedTypeApi> {
    pub id: u64,
    pub author: ManagedAddress<M>,
    pub title: ManagedBuffer<M>,
    pub body: ManagedBuffer<M>,
    pub timestamp: u64,
    pub parent_id: u64,
}

#[type_abi]
#[derive(TopEncode, TopDecode, NestedEncode, NestedDecode, Clone)]
pub struct PostWithUpvotes<M: ManagedTypeApi> {
    pub post: Post<M>,
    pub upvotes: u64,
}
