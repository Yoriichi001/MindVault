import os
from App import create_app, db
from App.models import User, Material, Feedback

app = create_app()

def seed_database():
    """Seeds default master administrator, sample scholar, and curated library materials."""
    with app.app_context():
        # 1. Ensure E_Cell_Admin_Panel has Master Administrator authority
        ecell_admin = User.query.filter(
            (User.username.ilike('E_Cell_Admin_Panel')) | (User.email == 'ecell.cup@gmail.com')
        ).first()
        if not ecell_admin:
            ecell_admin = User(
                username='E_Cell_Admin_Panel',
                email='ecell.cup@gmail.com',
                role='admin',
                is_verified=True,
                is_active=True,
                avatar='default-avatar.png'
            )
            # Retain the exact verified bcrypt hash for the master administrator
            ecell_admin.password_hash = '$2b$12$lWanCuX88B.8MwQXvny2b.x/Vsak.eHV.4iu4sH1/c7jjig3RY3Pa'
            db.session.add(ecell_admin)
            app.logger.info("Created Master Administrator: E_Cell_Admin_Panel (ecell.cup@gmail.com)")
        else:
            ecell_admin.role = 'admin'
            ecell_admin.is_verified = True
            ecell_admin.is_active = True

        # Permanently purge any generic 'admin' / 'admin@mindvault.edu' account to prevent guessing attacks
        generic_admin = User.query.filter(
            (User.username == 'admin') | (User.email == 'admin@mindvault.edu')
        ).first()
        if generic_admin:
            db.session.delete(generic_admin)

        # 2. Create Sample Student if none exists
        student = User.query.filter_by(email='student@mindvault.edu').first()
        if not student:
            student = User(
                username='scholar_student',
                email='student@mindvault.edu',
                role='student',
                is_verified=True,
                is_active=True,
                avatar='default-avatar.png'
            )
            student.set_password('StudentPassword123!')
            db.session.add(student)
            app.logger.info("Created default Scholar Student: student@mindvault.edu / StudentPassword123!")

        db.session.commit()

        # 3. Create Sample Library Materials if table is empty
        if Material.query.count() == 0:
            materials = [
                # BOOKS
                Material(
                    title="Structure & Interpretation of Computer Programs",
                    author="Harold Abelson & Gerald Jay Sussman",
                    category="Books",
                    sub_category="Computer Science",
                    description="A foundational masterpiece of computer science education. It explores recursive procedures, computational abstractions, data structures, and the formulation of computational processes through Lisp and Scheme.",
                    content_preview="A computer language is not just a way of getting a computer to perform operations, but rather that it is a novel formal medium for expressing ideas about methodology.",
                    full_content="""CHAPTER I: BUILDING ABSTRACTIONS WITH PROCEDURES
Computational processes are abstract beings that inhabit computers. As they evolve, processes manipulate other abstract things called data. The evolution of a process is directed by a pattern of rules called a program. People create programs to direct processes. In effect, we conjure the spirits of the computer with our spells.

A computational process, in a computer, is indeed much like a sorcerer's idea of a spirit. It cannot be seen or touched. It doesn't contain matter at all. However, it is very real. It can do intellectual work. It can answer questions. It can affect the world by disbursing money at a bank or by controlling a robot arm in a factory. The programs we use to conjure processes are like a sorcerer's spells.
---PAGE---
CHAPTER II: THE ELEMENTS OF PROGRAMMING
A powerful programming language is more than just a means for instructing a computer to perform tasks. The language also serves as a framework within which we organize our ideas about processes. Thus, when we describe a language, we should pay particular attention to the means that the language provides for combining simple ideas to form more complex ideas.

Every powerful language has three mechanisms for achieving this:
1. Primitive expressions, which represent the simplest entities the language is concerned with.
2. Means of combination, by which compound elements are built from simpler ones.
3. Means of abstraction, by which compound elements can be named and manipulated as units.
---PAGE---
CHAPTER III: COMPOUND DATA & HIERARCHICAL STRUCTURES
We have seen how primitive expressions can be combined to form compound procedures. But that alone does not suffice for constructing complex systems. We also need to represent composite data entities. By binding data items together into pairs and trees, we build computational structures that model complex phenomena with mathematical fidelity.""",
                    cover_image="https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=800&q=80",
                    file_path="books/sicp.pdf",
                    file_size_mb=2.4,
                    pages=657,
                    views_count=142,
                    downloads_count=38,
                    is_featured=True
                ),
                Material(
                    title="Principles of Quantum Mechanics",
                    author="Paul A. M. Dirac",
                    category="Books",
                    sub_category="Theoretical Physics",
                    description="The definitive treatise on quantum theory by one of its principal founders. Formulates the transformation theory, bra-ket notation, and relativistic wave mechanics that unified wave-particle duality.",
                    content_preview="The fundamental laws of nature do not govern the world as it appears in our mental picture in any very direct way, but rather they control a substratum of which we cannot form a mental picture without introducing irrelevancies.",
                    full_content="""PREFACE TO THE TREATISE ON QUANTUM MECHANICS
The methods of progress in theoretical physics have undergone a vast change during the present century. The classical tradition was to consider and study models of the universe built up out of concepts which were familiar to us in our everyday experience.

This older point of view has had to be abandoned in atomic and subatomic domains. It has become increasingly evident that nature operates on an entirely different scale, where observable measurements disturb the fundamental state of the particle under examination.
---PAGE---
THE PRINCIPLE OF SUPERPOSITION
The principle of superposition of states forms the cornerstone upon which all quantum mechanics rests. When an atomic system is in a state such that a measurement will certainly yield a specific result, we represent it mathematically by an eigenstate vector in an abstract Hilbert vector space.

Let us denote these states by the symbolic bracket notation |ψ⟩. Any linear combination of such states c₁|ψ₁⟩ + c₂|ψ₂⟩ represents another physically realizable state of the physical system, bearing probabilistic amplitudes of observation.
---PAGE---
RELATIVISTIC EQUATIONS OF THE ELECTRON
When combining the principles of special relativity with quantum mechanics, one requires an equation linear in both temporal and spatial derivatives. This leads inexorably to four-component wave functions and the prediction of antimatter, confirming the profound symmetry of nature's laws.""",
                    cover_image="https://images.unsplash.com/photo-1532094349884-543bc11b234d?auto=format&fit=crop&w=800&q=80",
                    file_path="books/quantum.pdf",
                    file_size_mb=1.8,
                    pages=314,
                    views_count=98,
                    downloads_count=24,
                    is_featured=True
                ),

                # RESEARCH PAPERS
                Material(
                    title="Attention Is All You Need",
                    author="Ashish Vaswani, Noam Shazeer, Niki Parmar et al.",
                    category="Research Papers",
                    sub_category="Artificial Intelligence & NLP",
                    description="The groundbreaking research publication introducing the Transformer architecture. Discarding recurrent and convolutional neural networks entirely, it relies entirely on self-attention mechanisms to compute representations of input and output.",
                    content_preview="We propose the Transformer, a model architecture eschewing recurrence and instead relying entirely on an attention mechanism to draw global dependencies between input and output.",
                    full_content="""ABSTRACT
The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.

Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train.
---PAGE---
1. INTRODUCTION
Recurrent neural networks, long short-term memory (LSTM) and gated recurrent neural networks have been firmly established as state-of-the-art approaches in sequence modeling. Recurrent models typically factor computation along the symbol positions of the input and output sequences. This sequential nature precludes parallelization within training examples, which becomes critical at longer sequence lengths.

In this work we propose the Transformer, which eschews recurrence and instead relies entirely on an attention mechanism to draw global dependencies between input and output. The Transformer allows for significantly more parallelization and can reach a new state of the art in translation quality after being trained for as little as twelve hours.
---PAGE---
2. SCALED DOT-PRODUCT ATTENTION
We call our particular attention 'Scaled Dot-Product Attention'. The input consists of queries and keys of dimension d_k, and values of dimension d_v. We compute the dot products of the query with all keys, divide each by √d_k, and apply a softmax function to obtain the weights on the values.

In practice, we compute the attention function on a set of queries simultaneously, packed together into a matrix Q. The keys and values are also packed into matrices K and V:
Attention(Q, K, V) = softmax(QK^T / √d_k) * V""",
                    cover_image="https://images.unsplash.com/photo-1507668077129-56e32842fceb?auto=format&fit=crop&w=800&q=80",
                    file_path="books/transformer.pdf",
                    file_size_mb=0.9,
                    pages=15,
                    views_count=320,
                    downloads_count=115,
                    is_featured=True
                ),
                Material(
                    title="A Mathematical Theory of Communication",
                    author="Claude E. Shannon",
                    category="Research Papers",
                    sub_category="Information Theory",
                    description="The seminal 1948 Bell System Technical Journal paper that founded the field of Information Theory. Defined the bit, entropy of information sources, channel capacity, and the fundamental limits of data compression and error correction.",
                    content_preview="The fundamental problem of communication is that of reproducing at one point either exactly or approximately a message selected at another point.",
                    full_content="""SECTION 1: DISCRETE NOISELESS SYSTEMS
The fundamental problem of communication is that of reproducing at one point either exactly or approximately a message selected at another point. Frequently the messages have meaning; that is they refer to or are correlated according to some system with certain physical or conceptual entities.

These semantic aspects of communication are irrelevant to the engineering problem. The significant aspect is that the actual message is one selected from a set of possible messages. The system must be designed to operate for each possible selection, not just the one which will actually be chosen.
---PAGE---
SECTION 2: ENTROPY OF AN INFORMATION SOURCE
Can we define a quantity which will measure, in some sense, how much information is produced by such a process, or better, at what rate information is produced? Suppose we have a set of possible events whose probabilities of occurrence are p₁, p₂, ..., p_n.

A reasonable measure of uncertainty H satisfies:
H = -K ∑ p_i * log₂(p_i)
Quantities of the form H = -∑ p * log(p) play a central role in information theory as measures of information, choice, and uncertainty, mirroring the thermodynamic concept of entropy established by Boltzmann and Gibbs.""",
                    cover_image="https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80",
                    file_path="books/shannon.pdf",
                    file_size_mb=1.2,
                    pages=55,
                    views_count=180,
                    downloads_count=64,
                    is_featured=False
                ),

                # STUDY MATERIALS
                Material(
                    title="Data Structures & Algorithms: Complete Synthesis",
                    author="MindVault Academic Editorial Board",
                    category="Study Materials",
                    sub_category="Computer Science & Engineering",
                    description="Comprehensive revision notes and algorithmic blueprints covering asymptotic analysis (Big-O, Big-Omega), balanced search trees, graph traversals (Dijkstra, Bellman-Ford, A*), and dynamic programming paradigms.",
                    content_preview="Mastery of algorithms separates the ordinary coder from the architect of high-performance computing systems.",
                    full_content="""MODULE 1: ASYMPTOTIC COMPLEXITY & RECURRENCE RELATIONS
In analyzing algorithmic performance, we abstract away machine architecture and focus on growth rates as input size n approaches infinity.
- Big-O Notation (O): Asymptotic upper bound.
- Big-Omega Notation (Ω): Asymptotic lower bound.
- Big-Theta Notation (Θ): Asymptotically tight bound.

The Master Theorem provides a cookbook method for solving divide-and-conquer recurrences of the form:
T(n) = a * T(n/b) + f(n)
Where a ≥ 1 and b > 1 describe the branching factor and problem division.
---PAGE---
MODULE 2: BALANCED SEARCH TREES (AVL & RED-BLACK)
Binary Search Trees suffer from O(n) degradation when keys are inserted monotonically. Balanced trees maintain an invariant guaranteeing O(log n) worst-case search, insertion, and deletion:
1. AVL Trees: Enforce that the height difference between left and right subtrees (Balance Factor) never exceeds ±1 through single and double rotations.
2. Red-Black Trees: Use a coloring invariant ensuring no two consecutive red nodes appear and every root-to-leaf path contains equal black depth.
---PAGE---
MODULE 3: GRAPH THEORY & SHORTEST PATHS
Graphs model networks, dependencies, and state spaces:
- Breadth-First Search (BFS): Computes unweighted shortest paths in O(V + E).
- Dijkstra's Algorithm: Computes non-negative weighted shortest paths using a Min-Priority Heap in O((V + E) log V).
- Bellman-Ford: Handles negative edge weights and detects negative weight cycles in O(V * E).""",
                    cover_image="https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=800&q=80",
                    file_path="books/dsa.pdf",
                    file_size_mb=1.5,
                    pages=42,
                    views_count=210,
                    downloads_count=89,
                    is_featured=True
                ),
                Material(
                    title="Linear Algebra & Matrix Decompositions for ML",
                    author="Dr. Elena Rostova",
                    category="Study Materials",
                    sub_category="Mathematics & Machine Learning",
                    description="Rigorous study guide and summary sheets for students diving into vector spaces, inner products, eigenvalue decomposition, Principal Component Analysis (PCA), and Singular Value Decomposition (SVD).",
                    content_preview="Matrices are not just grids of numbers; they are geometric transformations that stretch, rotate, and project high-dimensional space.",
                    full_content="""SECTION I: VECTOR SPACES, SUBSPACES & PROJECTIONS
A vector space over the field of real numbers ℝ consists of a set V along with operations of vector addition and scalar multiplication satisfying the eight field axioms.

For any matrix A ∈ ℝ^(m × n):
- The Column Space C(A) consists of all linear combinations of the column vectors.
- The Nullspace N(A) consists of all solutions to Ax = 0.
The Fundamental Theorem of Linear Algebra dictates that dim(C(A)) + dim(N(A)) = n (Rank-Nullity Theorem).
---PAGE---
SECTION II: EIGENVALUES & SINGULAR VALUE DECOMPOSITION (SVD)
Every real symmetric matrix can be orthogonally diagonalized:
A = Q * Λ * Q^T
For any rectangular matrix A ∈ ℝ^(m × n), the Singular Value Decomposition expresses A as:
A = U * Σ * V^T
Where U and V are orthogonal matrices containing the left and right singular vectors, and Σ is a diagonal matrix containing singular values σ₁ ≥ σ₂ ≥ ... ≥ 0.
This provides the mathematical basis for low-rank matrix approximation, Latent Semantic Analysis, and Principal Component Analysis (PCA).""",
                    cover_image="https://images.unsplash.com/photo-1509228468518-180dd4864904?auto=format&fit=crop&w=800&q=80",
                    file_path="books/linalg.pdf",
                    file_size_mb=1.1,
                    pages=28,
                    views_count=165,
                    downloads_count=52,
                    is_featured=False
                )
            ]

            for mat in materials:
                db.session.add(mat)
            db.session.commit()
            app.logger.info("Successfully seeded curated MindVault library materials.")

        # 4. Create sample initial feedback if empty
        if Feedback.query.count() == 0:
            sample_feedback = Feedback(
                name="Prof. Harrison Vance",
                email="h.vance@oxford-archive.org",
                subject="Commendation on MindVault Architecture",
                message="The in-browser antique reading experience and immediate access to both research papers and foundational textbooks is extraordinary. A triumph for open digital scholarship.",
                rating=5,
                is_read=True
            )
            db.session.add(sample_feedback)
            db.session.commit()

# Run database auto-seeding safely
try:
    seed_database()
except Exception as e:
    app.logger.warning(f"Database auto-seed check deferred: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
