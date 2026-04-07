document.addEventListener("DOMContentLoaded",()=>{
    showPosts();
    document.getElementById("create-link")?.addEventListener("click",showCreate)
    document.getElementById("following-link")?.addEventListener("click",()=>showPosts(true))
    document.getElementById("my-profile-link")?.addEventListener("click",()=>showProfile(username))
})
function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

async function fetchWithCSRF(url, options={}) {
    options.headers = options.headers || {};
    if (!csrfSafeMethod(options.method)) {
        options.headers['X-CSRFToken'] = csrftoken;
    }
    return fetch(url, options);
}
const showPosts=(following=false)=> {
    hideAll();
    document.getElementById("posts-container").style.display = "block";
    loadPosts(following,1,"posts-container");
}

const showProfile=(username)=> {
    hideAll();
    document.getElementById("profile-container").style.display = "block";
    getProfile(username);
    
}

const showCreate=()=> {
    hideAll();
    document.getElementById("add-post-container").style.display = "block";
    savePostElement()
}
const hideAll=()=> {
    document.getElementById("posts-container").style.display = "none";
    document.getElementById("profile-container").style.display = "none";
    document.getElementById("add-post-container").style.display = "none";
}


const loadPosts=(following,page=1,containerId)=>{
    fetch(`/posts?following=${following}&page=`+page)
    .then(res=>res.json())
    .then(data=>{
        const container=document.querySelector(`#${containerId}`)
        container.innerHTML=""
        if(data.posts.length==0){
            container.innerText="There is no post."
            return;
        }
        data.posts.forEach(post => {
            container.appendChild(createPostElement(post))
        });
        container.appendChild(createNavigationElement())
        container.querySelector(".next-btn").onclick = () => loadPosts(following, page + 1,containerId);
        container.querySelector(".prev-btn").onclick = () => {
            if (page > 1) loadPosts(following, page - 1,containerId);
        };
    })
}
const createNavigationElement=()=>{
    const template=document.querySelector("#navigation-template")
    const clone=template.content.cloneNode(true);
    return clone
}
const createPostElement=(post)=>{
   
    const template = document.querySelector("#post-template");
    const clone = template.content.cloneNode(true);
    const root=clone.querySelector(".post")
    clone.querySelector(".username").addEventListener("click",()=>showProfile(post.user))
    clone.querySelector(".username").innerText = post.user;
    clone.querySelector(".avatar").innerText = post.user.slice(0,2);
    clone.querySelector(".content").innerText = post.content;
    clone.querySelector(".timestamp").innerText = post.timestamp;
    if (isAuthenticated){
        const likeBtn = clone.querySelector(".btn-like");
        likeBtn.style.display = "inline";
        likeBtn.classList.toggle('liked', post.is_liked);
        likeBtn.onclick = (e) => toggleLike(post.id,e); 
    }
    const likesCount = clone.querySelector(".likes-count");
    console.log(likesCount)
    likesCount.innerText = post.likes_count;
    if (isAuthenticated && post.user    ==username){
        const editBtn = clone.querySelector(".btn-edit");
        editBtn.style.display = "inline";
        editBtn.onclick = (e) => editPostElement(post.id,e);
    }
    

    return clone;
}
const toggleLike=(postId,e)=> {
    fetchWithCSRF(`/like/${postId}`, {
        method: "PUT"
    })         
    .then(response => response.json())
    .then(data => {
        console.log(data)
        const root = e.target.closest(".post");

        count=root.querySelector(".likes-count")
        count.innerText = data.likes_count;

        const likeBtn = root.querySelector(".btn-like")
        likeBtn.classList.toggle('liked', data.liked);
    });
}
function toggleFollow(userId) {
    fetchWithCSRF(`/follow/${userId}`, {
        method: "PUT"
    })         
    .then(response => response.json())
    .then(data => {
        console.log(data)
        const btn = document.getElementById("follow-btn");
        btn.innerText = data.following ? "Unfollow" : "Follow";        
        document.getElementById("followers-count").innerText = data.followers_count;
    });
}
const editPostElement=(postId,e)=> {
    const postDiv = e.target.closest(".post");
    const content = postDiv.querySelector(".content").innerText;
    
    const textarea=createTextAreaUI(content,(content)=>{
        editPost(content,postId)
    })
    postDiv.replaceWith(textarea)

    
}
const savePostElement=()=> {
    const container=document.querySelector("#add-post-container");
    container.innerHTML=""
    const textarea=createTextAreaUI("",(content)=>{
        createPost(content)
    })
    container.appendChild(textarea)

}
const createTextAreaUI=(initialValue,onSave)=>{
    
    const template = document.querySelector("#add-post-template");
    const clone = template.content.cloneNode(true);
    
    const btn = clone.querySelector(".btn-save");
    const textarea= clone.querySelector(".content");
    textarea.value=initialValue
    btn.onclick =()=>{
        if (textarea.value!=0){
            onSave(textarea.value)
        }
    };

    return clone
}
const editPost=(content,postId)=> {     
    fetchWithCSRF(`/edit/${postId}`, {
        method: "PUT",
        body: JSON.stringify({ content: content })
    })
    .then(response => response.json())
    .then(() =>showPosts());
}
const createPost=(content)=> {
    fetchWithCSRF("/create", {
        method: "POST",
        body: JSON.stringify({ content: content })
    })
    .then(response => console.log(response.json()))
    .then(() => {
        showProfile(username);
    })
    .catch(err=>console.log(err))
}
const loadProfile=(data,page)=>{
        console.log(data)
        document.getElementById("username").innerText = data.profile_user.username;
        document.getElementById("followers-count").innerText = data.followers_count;
        document.getElementById("following-count").innerText = data.following_count;

        if (isAuthenticated && username!==data.profile_user.username){
            const btn = document.getElementById("follow-btn");
            btn.style.display = "inline";
            btn.innerText = data.is_following ? "Unfollow" : "Follow";
            btn.onclick = () => toggleFollow(data.profile_user.id);
        }
       

        // Posts
        const container = document.getElementById("profile-posts-container");
        container.innerHTML = "";
        data.posts.forEach(post => {
            container.appendChild(createPostElement(post))
        });
        container.appendChild(createNavigationElement())
        container.querySelector(".next-btn").onclick = () => loadProfile(username, page + 1);
        container.querySelector(".prev-btn").onclick = () => {
            if (page > 1) loadProfile(username, page - 1);
        };
}
const getProfile=(username,page=1)=>{
    fetch(`/profile/${username}?page=${page}`)
    .then(res=>res.json())
    .then(data=>loadProfile(data,page))
}