import {useState, useEffect, useMemo} from 'react'
import axios from 'axios';
import Slider from '../components/Slider';

const URL = 'http://localhost:8000/posts';

function Posts() {
    const [posts, setPosts] = useState([])
    const [countPosts, setCountPosts] = useState(5)
    // const [useAxios, setUseAxios] = useState(false);

    const [useAxios, setUseAxios] = useState(() => {
        const saved = localStorage.getItem('useAxios');
        return saved ? JSON.parse(saved) : false;
    });

    const fetchPosts = async () => {
                const response = await fetch(URL)
                console.log('Fetch response:', response);
                const data = await response.json()
                setPosts(data)
        }

    const axiosPosts = async () => {
        const response = await axios.get(URL)
        console.log('Axios response:', response);
        setPosts(response.data)
    }

    useEffect(() => {
        localStorage.setItem('useAxios', JSON.stringify(useAxios));

        if (useAxios) {
        axiosPosts();
        } else {
        fetchPosts();
        }
    }, [useAxios]);


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
                    <div className='post-card' key={post.id}>
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