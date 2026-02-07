#![no_std]
#![allow(clippy::all)]

mod post;

use multiversx_sc::imports::*;
use post::Post;

const MAX_LATEST_POSTS: u64 = 50;

#[multiversx_sc::contract]
pub trait BulletinBoard {
    #[init]
    fn init(&self) {
        self.post_count().set(0u64);
    }

    #[upgrade]
    fn upgrade(&self) {}

    // ========== ENDPOINTS ==========

    #[endpoint(createPost)]
    fn create_post(&self, title: ManagedBuffer, body: ManagedBuffer) -> u64 {
        require!(!title.is_empty(), "Title cannot be empty");
        require!(!body.is_empty(), "Body cannot be empty");

        let caller = self.blockchain().get_caller();
        let timestamp = self.blockchain().get_block_timestamp();
        let post_id = self.post_count().get() + 1u64;

        let post = Post {
            id: post_id,
            author: caller.clone(),
            title,
            body,
            timestamp,
            parent_id: 0u64,
        };

        self.posts(post_id).set(&post);
        self.top_level_posts().push(&post_id);
        self.post_count().set(post_id);

        self.post_created_event(post_id, &caller, timestamp, 0u64);

        post_id
    }

    #[endpoint(replyToPost)]
    fn reply_to_post(&self, parent_id: u64, body: ManagedBuffer) -> u64 {
        require!(!body.is_empty(), "Body cannot be empty");
        require!(
            !self.posts(parent_id).is_empty(),
            "Parent post does not exist"
        );

        let caller = self.blockchain().get_caller();
        let timestamp = self.blockchain().get_block_timestamp();
        let post_id = self.post_count().get() + 1u64;

        let post = Post {
            id: post_id,
            author: caller.clone(),
            title: ManagedBuffer::new(),
            body,
            timestamp,
            parent_id,
        };

        self.posts(post_id).set(&post);
        self.replies(parent_id).push(&post_id);
        self.post_count().set(post_id);

        self.post_created_event(post_id, &caller, timestamp, parent_id);

        post_id
    }

    // ========== VIEWS ==========

    #[view(getPost)]
    fn get_post(&self, post_id: u64) -> Post<Self::Api> {
        require!(!self.posts(post_id).is_empty(), "Post does not exist");
        self.posts(post_id).get()
    }

    #[view(getLatestPosts)]
    fn get_latest_posts(&self, count: u64) -> MultiValueEncoded<Post<Self::Api>> {
        let capped_count = core::cmp::min(count, MAX_LATEST_POSTS);
        let mut result = MultiValueEncoded::new();
        let total = self.top_level_posts().len() as u64;

        if total == 0 {
            return result;
        }

        let start = if total > capped_count {
            total - capped_count
        } else {
            0u64
        };

        // VecMapper is 1-based: indexes 1..=len
        let start_index = start + 1;
        let end_index = total;

        for i in (start_index..=end_index).rev() {
            let post_id = self.top_level_posts().get(i as usize);
            let post = self.posts(post_id).get();
            result.push(post);
        }

        result
    }

    #[view(getReplies)]
    fn get_replies(&self, post_id: u64) -> MultiValueEncoded<Post<Self::Api>> {
        let mut result = MultiValueEncoded::new();
        let reply_count = self.replies(post_id).len();

        for i in 1..=reply_count {
            let reply_id = self.replies(post_id).get(i);
            let reply = self.posts(reply_id).get();
            result.push(reply);
        }

        result
    }

    #[view(getPostCount)]
    fn get_post_count(&self) -> u64 {
        self.post_count().get()
    }

    // ========== EVENTS ==========

    #[event("postCreated")]
    fn post_created_event(
        &self,
        #[indexed] post_id: u64,
        #[indexed] author: &ManagedAddress,
        #[indexed] timestamp: u64,
        parent_id: u64,
    );

    // ========== STORAGE ==========

    #[storage_mapper("postCount")]
    fn post_count(&self) -> SingleValueMapper<u64>;

    #[storage_mapper("posts")]
    fn posts(&self, post_id: u64) -> SingleValueMapper<Post<Self::Api>>;

    #[storage_mapper("topLevelPosts")]
    fn top_level_posts(&self) -> VecMapper<u64>;

    #[storage_mapper("replies")]
    fn replies(&self, parent_id: u64) -> VecMapper<u64>;
}
