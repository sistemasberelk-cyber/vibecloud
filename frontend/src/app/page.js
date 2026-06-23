'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('accessToken');
    if (!token) {
      router.push('/login');
    } else {
      router.push('/onboarding');
    }
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-[#050505]">
      <div className="flex flex-col items-center">
        <div className="w-16 h-16 border-4 border-t-purple-500 border-r-transparent border-b-blue-500 border-l-transparent rounded-full animate-spin"></div>
        <p className="mt-4 text-gray-400 font-mono tracking-widest text-sm">INICIALIZANDO SISTEMA...</p>
      </div>
    </div>
  );
}
