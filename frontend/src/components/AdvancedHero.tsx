import { useEffect, useRef } from 'react';

export default function AdvancedHero() {
  const mountRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let renderer: any = null;
    let frameId: number | null = null;
    let scene: any = null;
    let camera: any = null;
    let mesh: any = null;

    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    async function init() {
      const THREE = await import('three');

      const width = mountRef.current?.clientWidth || 600;
      const height = mountRef.current?.clientHeight || 320;

      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

      scene = new THREE.Scene();
      camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
      camera.position.z = 5;

      const geometry = new THREE.BoxGeometry(1.2, 1.2, 1.2);
      const material = new THREE.MeshStandardMaterial({ color: 0xc0392b });
      mesh = new THREE.Mesh(geometry, material);
      scene.add(mesh);

      const light = new THREE.DirectionalLight(0xffffff, 1);
      light.position.set(5, 10, 7.5);
      scene.add(light);

      if (mountRef.current) mountRef.current.appendChild(renderer.domElement);

      function animate() {
        if (!mesh) return;
        if (!prefersReduced) mesh.rotation.x += 0.01;
        if (!prefersReduced) mesh.rotation.y += 0.013;
        renderer.render(scene, camera);
        frameId = requestAnimationFrame(animate);
      }

      animate();
    }

    init();

    function cleanup() {
      if (frameId) cancelAnimationFrame(frameId);
      try {
        if (renderer) {
          renderer.forceContextLoss();
          renderer.domElement.remove();
          renderer.dispose();
        }
      } catch (e) {
        // ignore
      }
    }

    return cleanup;
  }, []);

  return <div ref={mountRef} style={{ width: '100%', height: 320, borderRadius: 8, overflow: 'hidden' }} />;
}
