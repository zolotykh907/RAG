import {useState, useEffect, useMemo} from 'react'
import axios from 'axios';
import Slider from '../components/Slider';

const POSTS_URL = 'https://jsonplaceholder.typicode.com/posts';

function Posts() {
    const [posts, setPosts] = useState([])
    const [countPosts, setCountPosts] = useState(5)
    const [useAxios, setUseAxios] = useState(false); // false = fetch, true = axios

    useEffect(() => {
        const fetchPosts = async () => {
                const response = await fetch(POSTS_URL)
                const data = await response.json()
                setPosts(data)
        }
        fetchPosts()
    }, [])

    const visiblePosts = useMemo(() => posts.slice(0, countPosts), [posts, countPosts]);

    return (
        <section>
            <h2> Посты</h2>
            <div className='posts-meta'>
                <Slider value={countPosts} onChange={setCountPosts} />
                <p className='slidebar-value'>{countPosts}</p>
            </div>

            <div className='posts-list'>
                {visiblePosts.map((post, index) => (
                    <div className='post-card'>
                        <span className='post-number'>{index + 1}</span>
                        <h3>{post.title}</h3>
                        <p>{post.body}</p>
                    </div>   
                ))}
            </div>
        </section>
    )
}


export default Posts