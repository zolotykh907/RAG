import {useState, useEffect, useMemo} from 'react'
import axios from 'axios';
import Slider from '../components/Slider';

const POSTS_URL = 'https://jsonplaceholder.typicode.com/posts';

function Posts() {
    const [posts, setPosts] = useState([])
    const [countPosts, setCountPosts] = useState(5)
    const [useAxios, setUseAxios] = useState(false); // false = fetch, true = axios

    const fetchPosts = async () => {
                const response = await fetch(POSTS_URL)
                const data = await response.json()
                setPosts(data)
        }

    const axiosPosts = async () => {
        const response = await axios.get(POSTS_URL)
        setPosts(response.data)
    }
    useEffect(() => {
        if (useAxios) {
            axiosPosts()
        }
        else {
            fetchPosts()
        }

    }, [useAxios])

    const visiblePosts = useMemo(() => posts.slice(0, countPosts), [posts, countPosts]);

    return (
        <section>
            <h2> Посты</h2>
            <div className='posts-config'>
                <div className="method-toggle">
                    <button
                        className={`method-btn ${!useAxios ? 'active' : ''}`}
                        onClick={() => setUseAxios(false)}
                    >
                        Fetch
                    </button>

                    <button
                        className={`method-btn ${useAxios ? 'active' : ''}`}
                        onClick={() => setUseAxios(true)}
                    >
                        Axios
                    </button>
                </div>
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